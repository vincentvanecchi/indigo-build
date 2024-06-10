module;
#include <libfswatch/c++/monitor_factory.hpp>
#include <cassert>
module fswatch;

namespace fswatch {
    Service::Service(const std::vector<std::string>& paths, const Configuration& conf) {        
        impl_ = fsw::monitor_factory::create_monitor(
            fsw_monitor_type::windows_monitor_type, 
            paths, 
            &Service::on_events_impl, 
            this
        );

        impl_->set_latency(static_cast<double>( conf.latency.count() ) / 1000);
        impl_->set_recursive(conf.recursive);

        assert(impl_ != nullptr);
    }

    Service::~Service() {
        reset();
    }
    
    Service::Service(Service&& o) noexcept
        : impl_(o.impl_) {
        o.impl_ = nullptr;
    }

    Service& Service::operator=(Service&& o) noexcept {
        impl_ = o.impl_;
        o.impl_ = nullptr;
        return *this;
    }

    void Service::swap(Service& o) noexcept {
        auto tmp{impl_};
        impl_ = o.impl_;
        o.impl_ = tmp;
    }

    void Service::reset() {
        if (up_ && watcher_.joinable()) {
            request_stop();
            watcher_.join();
        }

        assert(!up_);

        if (impl_) {
            delete impl_;
            impl_ = nullptr;
        }
    }

    void Service::start() {
        watcher_ = std::jthread([this](std::stop_token stop_token_) {
            try {
                assert(impl_ != nullptr);

                std::stop_callback stop_callback_(stop_token_, [this]() {
                    // stop fsw::monitor
                    {
                        std::unique_lock<std::mutex> lock_{mutex_};
                        if (impl_) {
                            impl_->stop();
                        }
                    }
                    
                    cond_.notify_all();
                });

                up_ = true;
                cond_.notify_one();

                impl_->start();

                up_ = false;
                cond_.notify_all();
            } catch (const std::exception&) {
                exception_ = std::current_exception();
            }
        });

        std::unique_lock<std::mutex> lock_{mutex_};
        cond_.wait(lock_, [this]() -> bool {
            return up_.load();
        });
    }

    bool Service::is_running() const noexcept {
        return up_;
    }
    
    std::stop_source Service::get_stop_source() noexcept {
        return watcher_.get_stop_source();
    }

    std::stop_token Service::get_stop_token() const noexcept {
        return watcher_.get_stop_token();
    }

    void Service::request_stop() {
        auto stop_source_ = watcher_.get_stop_source();
        if (stop_source_.stop_possible() && !stop_source_.stop_requested()) {
            stop_source_.request_stop();
        }
    }

    void Service::rethrow() {
        std::unique_lock<std::mutex> lock_{mutex_};
        if (auto exc = exception_; exc) {
            exception_ = std::exception_ptr();
            lock_.unlock();
            std::rethrow_exception(exc);
        }
    }

    bool Service::wait_events_for(std::chrono::milliseconds timeout) {
        std::unique_lock<std::mutex> lock_{mutex_};
        bool has_events_ = cond_.wait_for(lock_, timeout, [this]() -> bool {
            return !events_.empty();
        });
        return has_events_;
    }
    
    std::vector<Event> Service::pop_events() {
        std::vector<Event> events;
        std::unique_lock<std::mutex> lock_{mutex_};
        events.swap(events_);
        return events;
    }

    void Service::on_events_impl(const std::vector<fsw::event>& events, void* context) {
        Service* self = reinterpret_cast<Service*>(context);
        assert(self != nullptr && self->impl_ != nullptr);
        
        std::string moved_from_;
        std::unique_lock<std::mutex> lock_{self->mutex_};

        for (const auto& evt : events) {
            auto flags = evt.get_flags();
            if (flags.empty()) {
                continue;
            }
            
            Event base_event{
                evt.get_path(),
                std::string{},
                evt.get_time_point(),
                EventType::None
            };

            EventType event_type = EventType::None;
            switch (flags.front()) {
                case fsw_event_flag::Created: {
                    base_event.type = EventType::Create;
                    self->events_.push_back(std::move(base_event));
                    break;
                }
                case fsw_event_flag::Updated: {
                    base_event.type = EventType::Update;
                    self->events_.push_back(std::move(base_event));
                    break;
                }
                case fsw_event_flag::Removed: {
                    base_event.type = EventType::Remove;
                    self->events_.push_back(std::move(base_event));
                    break;
                }
                case fsw_event_flag::Renamed: {
                    if (flags.size() < 2) {
                        continue;
                    }

                    switch (flags.at(1)) {
                        case fsw_event_flag::MovedFrom: {
                            moved_from_ = std::move(base_event.path);
                            break;
                        }
                        case fsw_event_flag::MovedTo: {
                            assert(!moved_from_.empty());
                            base_event.moved_to = std::move(base_event.path);
                            base_event.path = std::move(moved_from_);
                            base_event.type = EventType::Move;
                            self->events_.push_back(base_event);
                            moved_from_.clear();
                            break;
                        }
                        default: {
                            // TODO: warning?
                            break;
                        }
                    }

                    break;
                }
                default: {
                    // TODO: warning?
                    break;
                }
            }

        }

        lock_.unlock();

        self->cond_.notify_one();
    }

} // namespace fswatch
