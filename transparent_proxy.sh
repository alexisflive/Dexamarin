#! /bin/bash
# enabling: adb shell "sh transparent_proxy.sh enable proxy_ip:proxy_port"
# disabling: adb shell "sh transparent_proxy.sh disable"

if [[ $1 == "enable" ]]; then
    # Flush current rules
    iptables -t nat -F

    # Disable IPv6
    echo 0 > /proc/sys/net/ipv6/conf/wlan0/accept_ra
    echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6

    # Enable IP forwarding
    sysctl -w net.ipv4.ip_forward=1

    # Disable ICMP redirects
    sysctl -w net.ipv4.conf.all.send_redirects=0

    # Redirect rules
    iptables -t nat -A OUTPUT -p tcp --dport 80 -j DNAT --to-destination $2
    iptables -t nat -A OUTPUT -p tcp --dport 443 -j DNAT --to-destination $2
    iptables -t nat -A POSTROUTING -p tcp --dport 80 -j MASQUERADE
    iptables -t nat -A POSTROUTING -p tcp --dport 443 -j MASQUERADE
elif [[ $1 == "disable" ]]; then
    # Flush current rules
    iptables -t nat -F

    # Disable IP forwarding
    sysctl -w net.ipv4.ip_forward=0

    # Enable ICMP redirects
    sysctl -w net.ipv4.conf.all.send_redirects=1
else
    echo 'arguments required: [enable|disable] [proxy_ip_address:proxy_port]'
fi