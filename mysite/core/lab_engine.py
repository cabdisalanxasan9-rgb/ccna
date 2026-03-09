import ipaddress
import json
from dataclasses import dataclass


SUPPORTED_PROTOCOLS = ("OSPF", "RIP", "EIGRP", "STATIC", "VLAN", "NAT", "PORT-SECURITY")


@dataclass
class LabInput:
    name: str
    routers: int
    switches: int
    pcs: int
    vlan_count: int
    ip_scheme: str
    protocols: list[str]
    difficulty: str


def normalize_protocols(protocols: list[str]) -> list[str]:
    clean = []
    seen = set()
    for item in protocols:
        p = item.strip().upper()
        if p in SUPPORTED_PROTOCOLS and p not in seen:
            clean.append(p)
            seen.add(p)
    if not clean:
        clean = ["OSPF"]
    return clean


def parse_ip_network(raw_network: str):
    try:
        return ipaddress.ip_network(raw_network, strict=False)
    except ValueError:
        return ipaddress.ip_network("192.168.0.0/16")


def build_subnet_plan(base_network: str, vlan_count: int) -> list[dict]:
    base = parse_ip_network(base_network)
    vlan_count = max(1, min(vlan_count, 32))

    target_prefix = max(base.prefixlen, 24)
    if target_prefix > 30:
        target_prefix = base.prefixlen

    try:
        all_subnets = list(base.subnets(new_prefix=target_prefix))
    except ValueError:
        all_subnets = [base]

    if len(all_subnets) < vlan_count:
        all_subnets = [base]

    plan = []
    for idx in range(vlan_count):
        subnet = all_subnets[idx % len(all_subnets)]
        hosts = list(subnet.hosts())
        gateway = str(hosts[0]) if hosts else str(subnet.network_address)
        usable_range = "n/a"
        if len(hosts) >= 2:
            usable_range = f"{hosts[0]} - {hosts[-1]}"
        plan.append(
            {
                "vlan_id": 10 + idx,
                "network": str(subnet.network_address),
                "prefix": subnet.prefixlen,
                "gateway": gateway,
                "usable_range": usable_range,
            }
        )
    return plan


def build_topology_text(lab: LabInput, subnet_plan: list[dict]) -> str:
    lines = [
        f"Lab Name: {lab.name}",
        f"Devices: {lab.routers} routers, {lab.switches} switches, {lab.pcs} PCs",
        f"Protocols: {', '.join(lab.protocols)}",
        "",
        "Suggested Layout:",
    ]

    for i in range(1, lab.routers + 1):
        lines.append(f"- Router R{i}")
    for i in range(1, lab.switches + 1):
        lines.append(f"- Switch SW{i}")
    for i in range(1, lab.pcs + 1):
        sw_num = min(i, lab.switches)
        lines.append(f"- PC{i} connected to SW{sw_num}")

    lines.append("")
    lines.append("Address Plan:")
    for item in subnet_plan:
        lines.append(
            f"- VLAN {item['vlan_id']}: {item['network']}/{item['prefix']} (GW {item['gateway']})"
        )

    return "\n".join(lines)


def build_topology_diagram(lab: LabInput) -> str:
    lines = ["Topology (Text Diagram)"]
    router_chain = " -- ".join([f"[R{i}]" for i in range(1, lab.routers + 1)])
    lines.append(router_chain if router_chain else "[R1]")

    for s in range(1, lab.switches + 1):
        attached_router = min(s, max(1, lab.routers))
        lines.append(f"  |\n [SW{s}] <-> [R{attached_router}]")

    for p in range(1, lab.pcs + 1):
        attached_sw = min(p, max(1, lab.switches))
        lines.append(f" [PC{p}] -> [SW{attached_sw}]")

    return "\n".join(lines)


def build_mermaid_topology(lab: LabInput) -> str:
    lines = ["graph LR"]

    for r in range(1, lab.routers + 1):
        lines.append(f"R{r}[Router R{r}]")
    for s in range(1, lab.switches + 1):
        lines.append(f"SW{s}[Switch SW{s}]")
    for p in range(1, lab.pcs + 1):
        lines.append(f"PC{p}[PC {p}]")

    for r in range(1, lab.routers):
        lines.append(f"R{r} --- R{r + 1}")

    for s in range(1, lab.switches + 1):
        attached_router = min(s, max(1, lab.routers))
        lines.append(f"SW{s} --- R{attached_router}")

    for p in range(1, lab.pcs + 1):
        attached_switch = min(p, max(1, lab.switches))
        lines.append(f"PC{p} --- SW{attached_switch}")

    return "\n".join(lines)


def analyze_error_output(raw_output: str) -> list[str]:
    text = raw_output.lower()
    findings = []

    if "administratively down" in text or "line protocol is down" in text:
        findings.append("Interface appears down. Check cable and run 'no shutdown' on correct interface.")
    if "invalid input detected" in text:
        findings.append("CLI syntax error detected. Re-check command spelling and IOS-specific command format.")
    if "ospf" in text and ("down" in text or "init" in text or "exstart" in text):
        findings.append("OSPF adjacency issue. Verify area ID, subnet mask, hello/dead timers, and network statements.")
    if "%ip address overlaps" in text or "overlaps with" in text:
        findings.append("Overlapping IP detected. Assign unique subnets per interface/VLAN.")
    if "native vlan mismatch" in text:
        findings.append("Trunk native VLAN mismatch. Align native VLAN on both trunk ends.")
    if "dhcp" in text and ("no address" in text or "failed" in text):
        findings.append("DHCP failure. Verify pool network, gateway, excluded range, and relay if needed.")
    if "deny" in text or "access-list" in text:
        findings.append("Traffic may be blocked by ACL. Validate ACL order and interface direction (in/out).")
    if "nat" in text and ("no translations" in text or "misses" in text):
        findings.append("NAT appears inactive. Check inside/outside interface roles and ACL match for NAT source.")

    if not findings:
        findings.append("No known pattern matched. Start with: interface status, IP/mask, gateway, routing table, then ACL/NAT.")
    return findings


def analyze_config_audit(config_text: str) -> list[str]:
    lines = [line.strip().lower() for line in config_text.splitlines() if line.strip()]
    text = "\n".join(lines)
    findings = []

    if not lines:
        return ["No config provided. Paste running-config or startup-config output for analysis."]

    if "interface" in text and "no shutdown" not in text:
        findings.append("Some interfaces may be shutdown. Add 'no shutdown' under required interfaces.")

    if "router ospf" in text:
        if "network " not in text:
            findings.append("OSPF process found but no network statements detected.")
        if "area" not in text:
            findings.append("OSPF area mapping looks incomplete. Confirm area IDs in network statements.")

    if "vlan" in text:
        has_trunk = "switchport mode trunk" in text
        if not has_trunk:
            findings.append("VLAN config detected without trunk configuration. Verify uplink trunk ports.")

    if "ip nat inside source" in text:
        if "ip nat inside" not in text or "ip nat outside" not in text:
            findings.append("NAT overload exists but inside/outside interface roles look incomplete.")

    acl_lines = [line for line in lines if line.startswith("access-list")]
    if acl_lines:
        permit_any_any = any("permit ip any any" in line for line in acl_lines)
        deny_exists = any("deny" in line for line in acl_lines)
        if deny_exists and not permit_any_any:
            findings.append("ACL has deny statements but no final permit rule. Traffic may be over-blocked.")

    interface_blocks = [line for line in lines if line.startswith("interface ")]
    ip_lines = [line for line in lines if line.startswith("ip address ")]
    if interface_blocks and not ip_lines and "switchport" not in text:
        findings.append("Layer 3 interface blocks found without IP addresses.")

    if "router rip" in text and "version 2" not in text:
        findings.append("RIP configured without 'version 2'. Consider RIP v2 for classless routing.")

    if "router eigrp" in text and "no auto-summary" not in text:
        findings.append("EIGRP configured without 'no auto-summary'. This can cause route issues.")

    if not findings:
        findings.append("No high-risk pattern found. Validate with show commands: interface brief, neighbors, routes, vlan, acl, nat.")

    return findings


def _router_interfaces(router_idx: int, routers: int) -> list[str]:
    interfaces = [
        "interface g0/0",
        f" ip address 192.168.{router_idx}.1 255.255.255.0",
        " no shutdown",
        "exit",
    ]

    if router_idx > 1:
        interfaces.extend(
            [
                "interface g0/1",
                f" ip address 10.10.{router_idx - 1}.2 255.255.255.252",
                " no shutdown",
                "exit",
            ]
        )

    if router_idx < routers:
        interfaces.extend(
            [
                "interface g0/2",
                f" ip address 10.10.{router_idx}.1 255.255.255.252",
                " no shutdown",
                "exit",
            ]
        )
    return interfaces


def build_cli_config(lab: LabInput, subnet_plan: list[dict]) -> str:
    blocks = []

    for r in range(1, lab.routers + 1):
        block = [
            f"! Router R{r}",
            "enable",
            "configure terminal",
            f"hostname R{r}",
            "no ip domain-lookup",
        ]
        block.extend(_router_interfaces(r, lab.routers))

        if "OSPF" in lab.protocols:
            block.extend(
                [
                    "router ospf 1",
                    f" router-id {r}.{r}.{r}.{r}",
                    f" network 192.168.{r}.0 0.0.0.255 area 0",
                ]
            )
            if r > 1:
                block.append(f" network 10.10.{r - 1}.0 0.0.0.3 area 0")
            if r < lab.routers:
                block.append(f" network 10.10.{r}.0 0.0.0.3 area 0")
            block.append("exit")

        if "RIP" in lab.protocols:
            block.extend(
                [
                    "router rip",
                    " version 2",
                    " no auto-summary",
                    f" network 192.168.{r}.0",
                    " network 10.0.0.0",
                    "exit",
                ]
            )

        if "EIGRP" in lab.protocols:
            block.extend(
                [
                    "router eigrp 100",
                    " no auto-summary",
                    f" network 192.168.{r}.0 0.0.0.255",
                    " network 10.10.0.0 0.0.255.255",
                    "exit",
                ]
            )

        if "STATIC" in lab.protocols and lab.routers >= 2:
            if r == 1:
                block.append("ip route 0.0.0.0 0.0.0.0 10.10.1.2")
            else:
                block.append("ip route 192.168.1.0 255.255.255.0 10.10.1.1")

        if "NAT" in lab.protocols and r == 1 and lab.routers >= 2:
            block.extend(
                [
                    "access-list 1 permit 192.168.0.0 0.0.255.255",
                    "interface g0/0",
                    " ip nat inside",
                    "exit",
                    "interface g0/2",
                    " ip nat outside",
                    "exit",
                    "ip nat inside source list 1 interface g0/2 overload",
                ]
            )

        block.extend(["end", "write memory", ""])
        blocks.append("\n".join(block))

    for s in range(1, lab.switches + 1):
        switch_block = [
            f"! Switch SW{s}",
            "enable",
            "configure terminal",
            f"hostname SW{s}",
            "no ip domain-lookup",
        ]

        if "VLAN" in lab.protocols:
            for vlan in subnet_plan:
                switch_block.extend(
                    [
                        f"vlan {vlan['vlan_id']}",
                        f" name VLAN_{vlan['vlan_id']}",
                    ]
                )
            switch_block.extend(
                [
                    "interface g0/1",
                    " switchport mode trunk",
                    " no shutdown",
                    "exit",
                ]
            )

        switch_block.extend(
            [
                "interface range fa0/2-10",
                " switchport mode access",
                " spanning-tree portfast",
            ]
        )

        if "PORT-SECURITY" in lab.protocols:
            switch_block.extend(
                [
                    " switchport port-security",
                    " switchport port-security maximum 2",
                    " switchport port-security violation restrict",
                    " switchport port-security mac-address sticky",
                ]
            )

        switch_block.extend(["exit", "end", "write memory", ""])
        blocks.append("\n".join(switch_block))

    return "\n".join(blocks)


def build_verification_steps(lab: LabInput) -> str:
    base = [
        "1. show ip interface brief",
        "2. show ip route",
        "3. ping between all LAN gateways",
        "4. ping PC-to-PC across different LANs",
    ]
    if "OSPF" in lab.protocols:
        base.insert(1, "show ip ospf neighbor")
    if "RIP" in lab.protocols:
        base.insert(1, "show ip rip database")
    if "EIGRP" in lab.protocols:
        base.insert(1, "show ip eigrp neighbors")
    if "NAT" in lab.protocols:
        base.append("5. show ip nat translations")
    if "VLAN" in lab.protocols:
        base.append("6. show vlan brief and show interfaces trunk")
    return "\n".join(base)


def build_troubleshooting_guide() -> str:
    return "\n".join(
        [
            "Step 1: Verify physical links and interface status (up/up).",
            "Step 2: Validate IP address, subnet mask, and default gateway on PCs.",
            "Step 3: Check routing protocol neighbors and learned routes.",
            "Step 4: Validate VLAN membership and trunk allowed VLANs.",
            "Step 5: Review ACL/NAT rules order and interface directions.",
            "Step 6: Re-test with ping and trace after each fix.",
        ]
    )


def build_learning_notes(protocols: list[str]) -> str:
    notes = {
        "OSPF": "OSPF is a link-state protocol that calculates shortest paths using SPF.",
        "RIP": "RIP is a distance-vector protocol that uses hop count as metric.",
        "EIGRP": "EIGRP uses DUAL algorithm and supports fast convergence.",
        "VLAN": "VLAN separates broadcast domains on switches for better segmentation.",
        "NAT": "NAT translates private IP addresses to public IP addresses.",
        "STATIC": "Static routes are manually configured and predictable.",
        "PORT-SECURITY": "Port security limits MAC addresses on access ports.",
    }
    selected = [f"- {p}: {notes[p]}" for p in protocols if p in notes]
    selected.append("- Routers forward packets between networks; switches forward frames inside LANs.")
    selected.append("- Most common errors: wrong mask, missing no shutdown, wrong VLAN, bad ACL direction.")
    return "\n".join(selected)


def build_suggestions(difficulty: str) -> list[str]:
    common = [
        "Create a lab with 2 routers, 3 VLANs, and OSPF area 0.",
        "Create a NAT lab for internet access scenario.",
        "Create a troubleshooting lab with one deliberate OSPF mismatch.",
    ]
    if difficulty == "advanced":
        common.extend(
            [
                "Build a multi-area OSPF lab with route summarization.",
                "Add ACL policy: Guest VLAN can access internet only.",
            ]
        )
    return common


def build_quiz(protocols: list[str], difficulty: str) -> list[dict]:
    quiz = [
        {
            "question": "Which command checks interface status quickly on Cisco routers?",
            "answer": "show ip interface brief",
        },
        {
            "question": "What is the purpose of a default gateway on a PC?",
            "answer": "It forwards traffic to remote networks.",
        },
    ]

    if "OSPF" in protocols:
        quiz.append(
            {
                "question": "Which command shows OSPF neighbors?",
                "answer": "show ip ospf neighbor",
            }
        )
    if "VLAN" in protocols:
        quiz.append(
            {
                "question": "Which command verifies VLAN membership on a switch?",
                "answer": "show vlan brief",
            }
        )
    if "NAT" in protocols:
        quiz.append(
            {
                "question": "Which command verifies active NAT mappings?",
                "answer": "show ip nat translations",
            }
        )

    if difficulty == "advanced":
        quiz.append(
            {
                "question": "Why is ACL rule order important?",
                "answer": "ACLs are matched top-down; first match wins.",
            }
        )
    return quiz[:6]


def generate_lab_payload(lab: LabInput) -> dict:
    lab.protocols = normalize_protocols(lab.protocols)
    subnet_plan = build_subnet_plan(lab.ip_scheme, lab.vlan_count)

    payload = {
        "topology_text": build_topology_text(lab, subnet_plan),
        "topology_diagram": build_topology_diagram(lab),
        "mermaid_topology": build_mermaid_topology(lab),
        "cli_config": build_cli_config(lab, subnet_plan),
        "verification_steps": build_verification_steps(lab),
        "troubleshooting_guide": build_troubleshooting_guide(),
        "learning_notes": build_learning_notes(lab.protocols),
        "subnet_plan": json.dumps(subnet_plan, indent=2),
        "quiz": build_quiz(lab.protocols, lab.difficulty),
        "suggestions": build_suggestions(lab.difficulty),
    }
    return payload
