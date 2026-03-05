#pragma once

#include "ClientPlatformSpecific.hpp"
#include "ManusSDK.h"
#include <mutex>
#include <vector>
#include <zmq.hpp>

enum class ConnectionType : int
{
    ConnectionType_Invalid = 0,
    ConnectionType_Integrated,
    ConnectionType_Local,
    ConnectionType_Remote,
};

enum class ClientReturnCode : int
{
    ClientReturnCode_Success = 0,
    ClientReturnCode_FailedPlatformSpecificInitialization,
    ClientReturnCode_FailedToInitialize,
    ClientReturnCode_FailedToFindHosts,
    ClientReturnCode_FailedToConnect,
    ClientReturnCode_FailedToShutDownSDK,
    ClientReturnCode_FailedPlatformSpecificShutdown,
};

class ClientRawSkeleton
{
public:
    RawSkeletonInfo info;
    std::vector<SkeletonNode> nodes;
};

class ClientRawSkeletonCollection
{
public:
    std::vector<ClientRawSkeleton> skeletons;
};

class ManusZMQ : public SDKClientPlatformSpecific
{
public:
    ManusZMQ();
    ~ManusZMQ();

    ClientReturnCode Initialize();
    ClientReturnCode InitializeSDK();
    ClientReturnCode ShutDown();
    ClientReturnCode RegisterAllCallbacks();
    void Run();

    static void OnRawSkeletonStreamCallback(const SkeletonStreamInfo* const p_RawSkeletonStreamInfo);

protected:
    ClientReturnCode Connect();

    static ManusZMQ* s_Instance;
    bool m_Running = true;
    ConnectionType m_ConnectionType = ConnectionType::ConnectionType_Invalid;

    std::mutex m_RawSkeletonMutex;
    ClientRawSkeletonCollection* m_NextRawSkeleton = nullptr;
    ClientRawSkeletonCollection* m_RawSkeleton = nullptr;

    uint32_t m_FrameCounter = 0;

    zmq::context_t* m_ZmqCtx  = nullptr;
    zmq::socket_t*  m_ZmqSock = nullptr;
};
