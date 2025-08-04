#!/bin/bash

echo "=== Emergency Network Diagnostic ==="
echo ""

echo "1. Checking localhost resolution:"
ping -c 1 localhost
echo ""

echo "2. Checking loopback interface:"
ifconfig lo0
echo ""

echo "3. Checking /etc/hosts file:"
cat /etc/hosts | grep -E "localhost|127.0.0.1"
echo ""

echo "4. Checking for listening ports:"
sudo lsof -i -P | grep LISTEN | head -10
echo ""

echo "5. Checking firewall status:"
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
echo ""

echo "6. Testing Python socket binding:"
python3 -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 12345))
    s.listen(1)
    print('SUCCESS: Can bind to 127.0.0.1:12345')
    s.close()
except Exception as e:
    print(f'FAILED: {e}')
"
echo ""

echo "=== Diagnostic Complete ==="