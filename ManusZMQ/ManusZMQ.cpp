#include "ManusZMQ.hpp"
#include "ClientLogging.hpp"
#include <iostream>
#include <thread>

using ManusSDK::ClientLog;

ManusZMQ* ManusZMQ::s_Instance = nullptr;

int main()
{
    ManusZMQ t_Client;
    if (t_Client.Initialize() != ClientReturnCode::ClientReturnCode_Success)
    {
        ClientLog::error("Failed to initialize.");
        return -1;
    }
    t_Client.Run();
    t_Client.ShutDown();
    return 0;
}

ManusZMQ::ManusZMQ()
{
    s_Instance = this;
}

ManusZMQ::~ManusZMQ()
{
    delete m_ZmqSock;
    delete m_ZmqCtx;
    s_Instance = nullptr;
}

ClientReturnCode ManusZMQ::Initialize()
{
    if (!PlatformSpecificInitialization())
        return ClientReturnCode::ClientReturnCode_FailedPlatformSpecificInitialization;

    const ClientReturnCode t_Result = InitializeSDK();
    if (t_Result != ClientReturnCode::ClientReturnCode_Success)
        return ClientReturnCode::ClientReturnCode_FailedToInitialize;

    m_ZmqCtx  = new zmq::context_t();
    m_ZmqSock = new zmq::socket_t(*m_ZmqCtx, zmq::socket_type::push);
    m_ZmqSock->bind("tcp://*:8000");
    ClientLog::print("ZMQ PUSH socket bound on tcp://*:8000");

    return ClientReturnCode::ClientReturnCode_Success;
}

ClientReturnCode ManusZMQ::InitializeSDK()
{
    ClientLog::print("[1] Integrated  [2] Local  [3] Remote");
    std::string t_Input;
    std::cin >> t_Input;

    switch (t_Input[0])
    {
        case '1': m_ConnectionType = ConnectionType::ConnectionType_Integrated; break;
        case '2': m_ConnectionType = ConnectionType::ConnectionType_Local;      break;
        case '3': m_ConnectionType = ConnectionType::ConnectionType_Remote;     break;
        default:
            ClientLog::print("Invalid input, try again");
            return InitializeSDK();
    }

    SDKReturnCode t_InitResult;
    if (m_ConnectionType == ConnectionType::ConnectionType_Integrated)
        t_InitResult = CoreSdk_InitializeIntegrated();
    else
        t_InitResult = CoreSdk_InitializeCore();

    if (t_InitResult != SDKReturnCode::SDKReturnCode_Success)
        return ClientReturnCode::ClientReturnCode_FailedToInitialize;

    const ClientReturnCode t_CbResult = RegisterAllCallbacks();
    if (t_CbResult != ClientReturnCode::ClientReturnCode_Success)
        return t_CbResult;

    CoordinateSystemVUH t_VUH;
    CoordinateSystemVUH_Init(&t_VUH);
    t_VUH.handedness = Side::Side_Right;
    t_VUH.up         = AxisPolarity::AxisPolarity_PositiveZ;
    t_VUH.view       = AxisView::AxisView_XFromViewer;
    t_VUH.unitScale  = 1.0f;

    if (CoreSdk_InitializeCoordinateSystemWithVUH(t_VUH, true) != SDKReturnCode::SDKReturnCode_Success)
        return ClientReturnCode::ClientReturnCode_FailedToInitialize;

    return ClientReturnCode::ClientReturnCode_Success;
}

ClientReturnCode ManusZMQ::ShutDown()
{
    if (CoreSdk_ShutDown() != SDKReturnCode::SDKReturnCode_Success)
        return ClientReturnCode::ClientReturnCode_FailedToShutDownSDK;

    if (!PlatformSpecificShutdown())
        return ClientReturnCode::ClientReturnCode_FailedPlatformSpecificShutdown;

    return ClientReturnCode::ClientReturnCode_Success;
}

ClientReturnCode ManusZMQ::RegisterAllCallbacks()
{
    if (CoreSdk_RegisterCallbackForRawSkeletonStream(*OnRawSkeletonStreamCallback) != SDKReturnCode::SDKReturnCode_Success)
    {
        ClientLog::error("Failed to register raw skeleton callback.");
        return ClientReturnCode::ClientReturnCode_FailedToInitialize;
    }
    return ClientReturnCode::ClientReturnCode_Success;
}

void ManusZMQ::Run()
{
    ClientLog::print("Connecting...");
    while (Connect() != ClientReturnCode::ClientReturnCode_Success)
    {
        ClientLog::print("Not connected, retrying in 1s.");
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    }

    CoreSdk_SetRawSkeletonHandMotion(HandMotion_Auto);
    ClientLog::print("Connected. Publishing on tcp://*:8000. Press space to exit.");

    while (m_Running)
    {
        m_RawSkeletonMutex.lock();
        delete m_RawSkeleton;
        m_RawSkeleton     = m_NextRawSkeleton;
        m_NextRawSkeleton = nullptr;
        m_RawSkeletonMutex.unlock();

        if (m_RawSkeleton && !m_RawSkeleton->skeletons.empty())
        {
            ClientLog::print("frame {} published ({} skeletons)", std::to_string(m_FrameCounter), std::to_string(m_RawSkeleton->skeletons.size()));
            m_FrameCounter++;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(33));

        if (GetKeyDown(' '))
            m_Running = false;
    }
}

ClientReturnCode ManusZMQ::Connect()
{
    bool t_Local = m_ConnectionType == ConnectionType::ConnectionType_Local;
    if (CoreSdk_LookForHosts(1, t_Local) != SDKReturnCode::SDKReturnCode_Success)
        return ClientReturnCode::ClientReturnCode_FailedToFindHosts;

    uint32_t t_Count = 0;
    if (CoreSdk_GetNumberOfAvailableHostsFound(&t_Count) != SDKReturnCode::SDKReturnCode_Success || t_Count == 0)
        return ClientReturnCode::ClientReturnCode_FailedToFindHosts;

    std::unique_ptr<ManusHost[]> t_Hosts(new ManusHost[t_Count]);
    if (CoreSdk_GetAvailableHostsFound(t_Hosts.get(), t_Count) != SDKReturnCode::SDKReturnCode_Success)
        return ClientReturnCode::ClientReturnCode_FailedToFindHosts;

    uint32_t t_Sel = 0;
    if (!t_Local && t_Count > 1)
    {
        ClientLog::print("Select host (1-{}):", t_Count);
        for (uint32_t i = 0; i < t_Count; i++)
            ClientLog::print("[{}] {} {}", i + 1, t_Hosts[i].hostName, t_Hosts[i].ipAddress);
        uint32_t t_In = 0;
        std::cin >> t_In;
        if (t_In < 1 || t_In > t_Count) return ClientReturnCode::ClientReturnCode_FailedToConnect;
        t_Sel = t_In - 1;
    }

    SDKReturnCode t_Res = CoreSdk_ConnectToHost(t_Hosts[t_Sel]);
    if (t_Res == SDKReturnCode::SDKReturnCode_NotConnected)
        return ClientReturnCode::ClientReturnCode_FailedToConnect;

    return ClientReturnCode::ClientReturnCode_Success;
}

/// @brief Called by the SDK when new raw skeleton data is available.
/// Formats each skeleton as: gloveId_hex,x,y,z,rx,ry,rz,rw,... (one entry per node)
/// and sends a single ZMQ message per skeleton per frame.
void ManusZMQ::OnRawSkeletonStreamCallback(const SkeletonStreamInfo* const p_Info)
{
    if (!s_Instance) return;

    ClientRawSkeletonCollection* t_Next = new ClientRawSkeletonCollection();
    t_Next->skeletons.resize(p_Info->skeletonsCount);

    for (uint32_t i = 0; i < p_Info->skeletonsCount; i++)
    {
        CoreSdk_GetRawSkeletonInfo(i, &t_Next->skeletons[i].info);
        t_Next->skeletons[i].nodes.resize(t_Next->skeletons[i].info.nodesCount);
        t_Next->skeletons[i].info.publishTime = p_Info->publishTime;
        CoreSdk_GetRawSkeletonData(i, t_Next->skeletons[i].nodes.data(), t_Next->skeletons[i].info.nodesCount);
    }

    // Format and publish before handing data off to the main thread.
    try
    {
        for (uint32_t j = 0; j < p_Info->skeletonsCount; j++)
        {
            char buf[8192] = {};
            char* pos = buf;
            int   len = 0;

            // glove id as hex prefix
            int n = sprintf(pos, "%x,", t_Next->skeletons[j].info.gloveId);
            pos += n; len += n;

            uint32_t t_NodeCount = t_Next->skeletons[j].info.nodesCount;
            for (uint32_t i = 0; i < t_NodeCount; i++)
            {
                const ManusVec3&       p = t_Next->skeletons[j].nodes[i].transform.position;
                const ManusQuaternion& r = t_Next->skeletons[j].nodes[i].transform.rotation;
                n = sprintf(pos, "%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,", p.x, p.y, p.z, r.x, r.y, r.z, r.w);
                pos += n; len += n;
            }

            // trim trailing comma
            if (len > 0) len--;

            s_Instance->m_ZmqSock->send(zmq::buffer(buf, len), zmq::send_flags::dontwait);
        }
    }
    catch (...) {}

    s_Instance->m_RawSkeletonMutex.lock();
    delete s_Instance->m_NextRawSkeleton;
    s_Instance->m_NextRawSkeleton = t_Next;
    s_Instance->m_RawSkeletonMutex.unlock();
}
