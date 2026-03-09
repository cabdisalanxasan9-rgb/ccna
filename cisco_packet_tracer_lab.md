# Cisco Packet Tracer Lab (2 Routers, 2 Switches, 4 PCs)

## Topology
- R1 g0/0 <-> SW1 g0/1
- R1 g0/1 <-> R2 g0/1
- R2 g0/0 <-> SW2 g0/1
- PC1 -> SW1 fa0/2
- PC2 -> SW1 fa0/3
- PC3 -> SW2 fa0/2
- PC4 -> SW2 fa0/3

## IP Plan
- R1-R2 link: 10.10.10.0/30
- VLAN 10: 192.168.10.0/24 (GW 192.168.10.1)
- VLAN 20: 192.168.20.0/24 (GW 192.168.20.1)
- VLAN 30: 192.168.30.0/24 (GW 192.168.30.1)
- VLAN 40: 192.168.40.0/24 (GW 192.168.40.1)

## SW1 Configuration
```cisco
enable
conf t
hostname SW1
no ip domain-lookup

vlan 10
 name USERS_A
vlan 20
 name USERS_B

interface fa0/2
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast

interface fa0/3
 switchport mode access
 switchport access vlan 20
 spanning-tree portfast

interface g0/1
 switchport mode trunk
 switchport trunk allowed vlan 10,20
 no shutdown
end
wr
```

## SW2 Configuration
```cisco
enable
conf t
hostname SW2
no ip domain-lookup

vlan 30
 name USERS_C
vlan 40
 name USERS_D

interface fa0/2
 switchport mode access
 switchport access vlan 30
 spanning-tree portfast

interface fa0/3
 switchport mode access
 switchport access vlan 40
 spanning-tree portfast

interface g0/1
 switchport mode trunk
 switchport trunk allowed vlan 30,40
 no shutdown
end
wr
```

## R1 Configuration
```cisco
enable
conf t
hostname R1
no ip domain-lookup

interface g0/1
 ip address 10.10.10.1 255.255.255.252
 no shutdown

interface g0/0
 no ip address
 no shutdown

interface g0/0.10
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0

interface g0/0.20
 encapsulation dot1Q 20
 ip address 192.168.20.1 255.255.255.0

ip dhcp excluded-address 192.168.10.1 192.168.10.20
ip dhcp excluded-address 192.168.20.1 192.168.20.20

ip dhcp pool VLAN10_POOL
 network 192.168.10.0 255.255.255.0
 default-router 192.168.10.1
 dns-server 8.8.8.8

ip dhcp pool VLAN20_POOL
 network 192.168.20.0 255.255.255.0
 default-router 192.168.20.1
 dns-server 8.8.8.8

router ospf 1
 router-id 1.1.1.1
 network 10.10.10.0 0.0.0.3 area 0
 network 192.168.10.0 0.0.0.255 area 0
 network 192.168.20.0 0.0.0.255 area 0

access-list 110 deny ip 192.168.20.0 0.0.0.255 192.168.10.0 0.0.0.255
access-list 110 permit ip any any

interface g0/0.20
 ip access-group 110 in
end
wr
```

## R2 Configuration
```cisco
enable
conf t
hostname R2
no ip domain-lookup

interface g0/1
 ip address 10.10.10.2 255.255.255.252
 no shutdown

interface g0/0
 no ip address
 no shutdown

interface g0/0.30
 encapsulation dot1Q 30
 ip address 192.168.30.1 255.255.255.0

interface g0/0.40
 encapsulation dot1Q 40
 ip address 192.168.40.1 255.255.255.0

ip dhcp excluded-address 192.168.30.1 192.168.30.20
ip dhcp excluded-address 192.168.40.1 192.168.40.20

ip dhcp pool VLAN30_POOL
 network 192.168.30.0 255.255.255.0
 default-router 192.168.30.1
 dns-server 8.8.8.8

ip dhcp pool VLAN40_POOL
 network 192.168.40.0 255.255.255.0
 default-router 192.168.40.1
 dns-server 8.8.8.8

router ospf 1
 router-id 2.2.2.2
 network 10.10.10.0 0.0.0.3 area 0
 network 192.168.30.0 0.0.0.255 area 0
 network 192.168.40.0 0.0.0.255 area 0
end
wr
```

## PC Setup
For PC1, PC2, PC3, PC4:
- Desktop > IP Configuration > DHCP

Expected:
- PC1: 192.168.10.x
- PC2: 192.168.20.x
- PC3: 192.168.30.x
- PC4: 192.168.40.x

## Verification Commands
On routers:
```cisco
show ip ospf neighbor
show ip route
show ip dhcp binding
show access-lists
```

On switches:
```cisco
show vlan brief
show interfaces trunk
```

## 10-Point Quick Checklist
1. All cables connected to correct ports.
2. Router interfaces are `no shutdown`.
3. SW1 has VLAN 10 and 20.
4. SW2 has VLAN 30 and 40.
5. Trunk ports on SW1 g0/1 and SW2 g0/1 are up.
6. Subinterfaces on R1 and R2 have correct dot1Q tags.
7. PCs receive DHCP addresses from correct VLAN ranges.
8. `show ip ospf neighbor` shows FULL adjacency between R1 and R2.
9. `show ip route` has OSPF-learned remote VLAN routes.
10. ACL test works: VLAN20 cannot ping VLAN10, but other inter-VLAN pings work.

---

## Basic Lab (OSPF Only)

Use this version if you want the easiest setup first.

### Basic Topology
- PC1, PC2 -> SW1 -> R1 g0/0
- PC3, PC4 -> SW2 -> R2 g0/0
- R1 g0/1 <-> R2 g0/1

### Basic IP Plan
- R1 g0/0: 192.168.10.1/24
- R1 g0/1: 10.10.10.1/30
- R2 g0/0: 192.168.20.1/24
- R2 g0/1: 10.10.10.2/30

PCs (static IP):
- PC1: 192.168.10.11/24, GW 192.168.10.1
- PC2: 192.168.10.12/24, GW 192.168.10.1
- PC3: 192.168.20.11/24, GW 192.168.20.1
- PC4: 192.168.20.12/24, GW 192.168.20.1

### R1 Basic Config
```cisco
enable
conf t
hostname R1
no ip domain-lookup

interface g0/0
 ip address 192.168.10.1 255.255.255.0
 no shutdown

interface g0/1
 ip address 10.10.10.1 255.255.255.252
 no shutdown

router ospf 1
 router-id 1.1.1.1
 network 192.168.10.0 0.0.0.255 area 0
 network 10.10.10.0 0.0.0.3 area 0
end
wr
```

### R2 Basic Config
```cisco
enable
conf t
hostname R2
no ip domain-lookup

interface g0/0
 ip address 192.168.20.1 255.255.255.0
 no shutdown

interface g0/1
 ip address 10.10.10.2 255.255.255.252
 no shutdown

router ospf 1
 router-id 2.2.2.2
 network 192.168.20.0 0.0.0.255 area 0
 network 10.10.10.0 0.0.0.3 area 0
end
wr
```

### Basic Verify
```cisco
show ip ospf neighbor
show ip route
```

Ping tests:
- PC1 -> PC3
- PC2 -> PC4

---

## Exam-Style Troubleshooting (Practice)

Use these as tasks. Break one item at a time, then fix it.

1. OSPF neighbor missing:
- Symptom: `show ip ospf neighbor` is empty.
- Check: link IPs, subnet mask, `network` statements, interfaces up.

2. Wrong VLAN tag:
- Symptom: PCs in one VLAN fail to reach gateway.
- Check: `encapsulation dot1Q` on router subinterface and switch access VLAN.

3. Trunk issue:
- Symptom: both VLANs on one switch fail.
- Check: `show interfaces trunk`, allowed VLAN list.

4. DHCP issue:
- Symptom: PC gets 169.254.x.x.
- Check: DHCP pool network, default-router, excluded range, gateway interface up.

5. ACL blocking too much:
- Symptom: all pings fail from VLAN20.
- Check: ACL order, deny/permit lines, interface/direction of `ip access-group`.

Useful troubleshooting commands:
```cisco
show run
show ip interface brief
show ip ospf neighbor
show ip route
show ip dhcp binding
show access-lists
show vlan brief
show interfaces trunk
```

---

## 7-Day Practice Plan

### Day 1: Basic Routing + OSPF
- Build the Basic Lab (OSPF only).
- Verify neighbors with `show ip ospf neighbor`.
- Do 4 ping tests between LANs.

### Day 2: VLAN Basics
- Create VLANs on SW1 and SW2.
- Assign PC ports to correct VLANs.
- Verify with `show vlan brief`.

### Day 3: Trunk + Router-on-a-Stick
- Configure trunk ports on both switches.
- Configure R1 and R2 subinterfaces with `encapsulation dot1Q`.
- Verify gateways from each VLAN.

### Day 4: DHCP
- Add DHCP pools on both routers.
- Set all PCs to DHCP.
- Verify leases using `show ip dhcp binding`.

### Day 5: OSPF Full Lab
- Enable OSPF for all VLAN networks.
- Confirm dynamic routes with `show ip route`.
- Test end-to-end ping between all PCs.

### Day 6: ACL Security
- Apply ACL to block VLAN20 -> VLAN10 only.
- Verify blocked and allowed traffic.
- Check counters in `show access-lists`.

### Day 7: Mock Exam (45-60 min)
- Rebuild full lab from zero without notes.
- Introduce 3 faults (wrong VLAN, wrong OSPF network, ACL misorder).
- Troubleshoot and fix using show/debug commands only.

### Daily Success Criteria
1. OSPF neighbors are FULL.
2. DHCP gives valid IPs.
3. Routing table has remote networks.
4. ACL behavior matches policy.
5. You can explain every command you used.

---

## Day 1 Practical Sheet (Basic OSPF)

Goal: Build a simple 2-router OSPF network and verify end-to-end connectivity.

Time target: 35-45 minutes

### Part A: Build and Configure (Hands-on)
1. Place devices:
- 2 routers, 2 switches, 4 PCs.

2. Cable devices:
- PC1/PC2 to SW1, PC3/PC4 to SW2.
- SW1 to R1 g0/0, SW2 to R2 g0/0.
- R1 g0/1 to R2 g0/1.

3. Configure router interfaces and OSPF (use Basic Lab section above).

4. Configure PC static IPs:
- PC1: 192.168.10.11 /24, GW 192.168.10.1
- PC2: 192.168.10.12 /24, GW 192.168.10.1
- PC3: 192.168.20.11 /24, GW 192.168.20.1
- PC4: 192.168.20.12 /24, GW 192.168.20.1

### Part B: Verify (Must pass)
Run these on both routers:
```cisco
show ip interface brief
show ip ospf neighbor
show ip route
```

Pass conditions:
1. All required interfaces are up/up.
2. One OSPF neighbor appears in FULL state.
3. Each router learns the remote LAN via OSPF (`O` route).
4. PC1 can ping PC3 and PC4.
5. PC2 can ping PC3 and PC4.

### Part C: Mini Quiz (No notes)
1. What command shows OSPF neighbors?
2. Why do we use wildcard mask in OSPF network command?
3. What does `O` mean in `show ip route`?
4. If ping fails but interfaces are up, what 2 things do you check first?
5. Which interface should hold the default gateway IP for a LAN?

### Part D: Quick Troubleshooting Drill
Break and fix each issue:
1. Shutdown R1 g0/1, then restore it.
2. Change one PC gateway to wrong IP, then correct it.
3. Remove one OSPF network statement, observe failure, add it back.

Commands to use:
```cisco
show run
show ip ospf neighbor
show ip route
show ip interface brief
```

### Answer Key (Mini Quiz)
1. `show ip ospf neighbor`
2. OSPF uses wildcard masks to match interface IP ranges to advertise.
3. `O` means route learned through OSPF.
4. Check IP addressing/subnet masks and routing/OSPF neighbor state.
5. The router LAN-facing interface (example: R1 g0/0 for LAN1).
