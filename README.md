# What is this?

`wgcheck` is a tool for monitoring the status of a Wireguard connection. It
periodically checks that it can access specific services through Wireguard, and
if any become inaccessible it runs an external tool to alert you to the
failure.

# How do I use it?

## Dependencies

First, you need some tools and configuration files:

- A Wireguard config file, as you would find in `/etc/wireguard`. Nothing
  particular required here, just that the config lets you access the services
  you want to monitor.

- `ip` (via `iproute2`) and `wg` (via `wireguard-tools`). `wgcheck` works by
  creating a network namespace that contains only the Wireguard interface, to
  avoid accidental leakage and force all service check connections to go over
  Wireguard (https://www.wireguard.com/netns/ explains the concept well).
  `wgcheck` has to create the Wireguard interface, create the namespace and move
  the interface into it, and configure the default route to use that interface.

- A service check tool. `wgcheck` itself does not know how to check whether a
  service is up. It delegates this to an external tool.

  - It is invoked without arguments.
  - A zero exit status indicates the service is up, any other exit status
    indicates the service is down. 
  - stdin is hooked up to `/dev/null`
  - stdout and stderr are passed through.
  - `checker` is run in a network namespace that only has access to the
    Wireguard interface. This makes it easy to avoid accidentally reporting a
    service as up (because you accessed it via the wrong interface), but
    it also means that `checker` may have a completely broken network. If you
    need a network connection apart from the specific service you are checking,
    consider creating a separate service and having `checker` communicate with it
    via some non-network means (Unix sockets, files, etc)

- An alert tool. As with service checking, `wgcheck` does not know how to
  notify you when the service is inaccessible.

  - It is invoked without arguments.
  - The exit status is ignored.
  - stdin is hooked up to `/dev/null`
  - stdout and stderr are passed through.

## Configuration

`wgcheck` is a shell script that dot sources its configuration from the file
you provide: `wgcheck CONFIG`

The `CONFIG` file supports these settings. See the `example.conf` file for an
example of a basic configuration.

- `netns_name` Required. The name of a network namespace. This gets passed to
  `ip netns add` and can only contain characters that are safe for filenames (the
  namespace is a special file inside the proc filesystem). If this network namespace
  already exists, `wgcheck` destroys and recreates it.

- `wg_name` Required. The name of the Wireguard interface to create. The Wireguard 
  interface is created in the root namespace first before being moved into the
  network namespace (this ensures it can use your host network interfaces for
  communicating with the Wireguard server). It must not conflict with any existing
  network interface.

- `wg_cidr` Required. The IP address and prefix to assign to the Wireguard interface.

- `wg_router` Required. The IP address to use for the default route on the Wireguard interface.

- `wg_conf` Required. The path of the Wireguard configuration file to use.

- `checker` Required. The executable to use as the checker. This must match the
  specification of the checker given in the **Dependencies** section. Note that
  this value is treated as a path and not a command: 
  `checker_exe=/usr/bin/ssh -v` does not treat `-v` as an argument.

- `alert` Required. The path to an executable matching the specification of the
  alert tool described in the **Dependencies** section. As with `checker`, this
  value is a path and not split.

- `tool_ip` Optional. The path to the `ip` executable. If not given, `wgcheck`
  uses the path returned from `command -v ip`.

- `tool_wg` Optional. The path to the `wg` executable. If not given, `wgcheck`
  uses the path returned from `command -v wg`.

# Why build this?

I run Wireguard at home to act both as a VPN for my machines, and also a secure
tunnel for general internet use. Wireguard itself is reliable: if I can connect
to the forwarded Wireguard port on my router, I get access to the server
running Wireguard.

Routing is more fragile since it depends on the wider state of the system:

- **sysctl** `net.ipv4.ip_forward=1` is a non-default setting. If `sysctl`
  did not apply my config for some reason then routing is impossible.

- **iptables** NAT and forwarding rules must be setup for traffic to go to
  other hosts. Maybe `iptables-persistent` didn't apply the rule properly, or
  some other event (like an Ansible deploy) caused `iptables` rules to be rebuilt
  without re-running `wg-quick`.

These issues are generally easy to fix but normally I don't know about them
until I need to use Wireguard for something. This script does proactive
monitoring so I can fix these issues before I leave home.
