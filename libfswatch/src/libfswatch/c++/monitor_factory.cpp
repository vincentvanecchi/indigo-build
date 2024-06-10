/*
 * Copyright (c) 2014-2021 Enrico M. Crisostomo
 *
 * This program is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation; either version 3, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <libfswatch/libfswatch_config.h>
#include <utility>
#include "libfswatch/c++/monitor_factory.hpp"
#include "libfswatch/c++/libfswatch_exception.hpp"

#if defined(HAVE_WINDOWS)
  #include "windows_monitor.hpp"
#endif

namespace fsw
{
  static monitor *create_default_monitor(std::vector<std::string> paths,
                                         FSW_EVENT_CALLBACK *callback,
                                         void *context)
  {
    fsw_monitor_type type;

    type = fsw_monitor_type::windows_monitor_type;

    return monitor_factory::create_monitor(type,
                                           std::move(paths),
                                           callback,
                                           context);
  }

  monitor *monitor_factory::create_monitor(fsw_monitor_type type,
                                           std::vector<std::string> paths,
                                           FSW_EVENT_CALLBACK *callback,
                                           void *context)
  {
    switch (type)
    {
      case system_default_monitor_type:
        return create_default_monitor(paths, callback, context);

#if defined(HAVE_WINDOWS)
      case windows_monitor_type:
        return new windows_monitor(paths, callback, context);
#endif
      default:
        throw libfsw_exception("Unsupported monitor.",
                              FSW_ERR_UNKNOWN_MONITOR_TYPE);
    }
  }

  std::map<std::string, fsw_monitor_type>& monitor_factory::creators_by_string()
  {
#define fsw_quote(x) #x
    static std::map<std::string, fsw_monitor_type> creator_by_string_set;

#if defined(HAVE_WINDOWS)
    creator_by_string_set[fsw_quote(windows_monitor)] = fsw_monitor_type::windows_monitor_type;
#endif

    return creator_by_string_set;
#undef fsw_quote
  }

  monitor *monitor_factory::create_monitor(const std::string& name,
                                           std::vector<std::string> paths,
                                           FSW_EVENT_CALLBACK *callback,
                                           void *context)
  {
    auto i = creators_by_string().find(name);

    if (i == creators_by_string().end())
      return nullptr;

    return create_monitor(i->second, std::move(paths), callback, context);
  }

  bool monitor_factory::exists_type(const std::string& name)
  {
    auto i = creators_by_string().find(name);

    return (i != creators_by_string().end());
  }

  std::vector<std::string> monitor_factory::get_types()
  {
    std::vector<std::string> types;

    for (const auto& i : creators_by_string())
    {
      types.push_back(i.first);
    }

    return types;
  }
}
