module;
#include "libfswatch/c++/monitor_factory.hpp"
#include <thread>
#include <mutex>
#include <atomic>
#include <stop_token>
#include <string_view>
#include <format>
export module fswatch;

export namespace fswatch {

    enum class EventType : uint32_t {
        None,
        Create,
        Update,
        Remove,
        Move
    };
    
    struct Event {
        std::string path;
        std::string moved_to;
        std::chrono::system_clock::time_point time_point;
        EventType type;
        uint8_t _padding_[4];

        inline std::string to_string() const {
            size_t ms = static_cast<size_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
                    time_point.time_since_epoch()
                ).count() % 1000
            );
                
            const char* type_;
            switch (type) {
                case EventType::Create: { type_ = "Create"; break; }
                case EventType::Update: { type_ = "Update"; break; }
                case EventType::Remove: { type_ = "Remove"; break; }
                case EventType::Move: { type_ = "Move"; break; }
                case EventType::None: [[fallthrough]];
                default: { type_ = "None"; break; }
            }

            constexpr std::string_view moved_to_left_{" -> \""};
            constexpr std::string_view moved_to_right_{"\""};

            return std::vformat("{:%Y.%m.%d %X}.{:0>3} {} :: \"{}\"{}{}{}", std::make_format_args(
                time_point, ms, type_, 
                path, 
                moved_to.empty() ? "" : moved_to_left_, moved_to.empty() ? "" : moved_to, moved_to.empty() ? "" : moved_to_right_
            ));
        }
    };

    struct Configuration {
        std::chrono::milliseconds latency{1000};
        bool recursive{true};
        uint8_t _padding_[7];
    };

    class Service {
        fsw::monitor* impl_{nullptr};
        std::jthread watcher_;
        std::vector<Event> events_;
        mutable std::mutex mutex_;
        std::condition_variable cond_;
        std::exception_ptr exception_;
        std::atomic<bool> up_{false};
        uint8_t _padding_[7];
    public:
        Service() = delete;

        explicit Service(const std::vector<std::string>& paths, const Configuration& conf = Configuration{});

        Service(const Service&) = delete;
        Service& operator=(const Service&) = delete;

        Service(Service&&) noexcept;
        Service& operator=(Service&&) noexcept;
        void swap(Service& o) noexcept;
        
        ~Service();
        void reset();

        void start();
        bool is_running() const noexcept;
        std::stop_source get_stop_source() noexcept;
        std::stop_token get_stop_token() const noexcept;
        void request_stop();
        void rethrow();

        bool wait_events_for(std::chrono::milliseconds timeout);
        std::vector<Event> pop_events();

    private:
        static void on_events_impl(const std::vector<fsw::event>& events, void* context);
    };

}
