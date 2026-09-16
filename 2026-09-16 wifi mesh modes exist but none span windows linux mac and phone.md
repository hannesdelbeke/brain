> [!summary] eli5
> zigbee devices relay traffic for each other with no hub in the middle, and this note explains why wifi does not work that way and what to run instead across a windows pc, a linux box, a mac and a phone.
> answered in full, nothing installed yet: wifi does have mesh modes, but no single one of them is implemented on all four of those platforms, so the working answer is an overlay network rather than a radio-level mesh.
> **needs from you:** decide whether to install [tailscale](https://tailscale.com/) on the windows pc, the linux box, the mac and the phone, recommend yes, it is the only option with first-party clients on all four and it takes about five minutes per device

> zigbee has some kind of mesh network where devices connect to each other. could we setup something similar with normal wifi? e.g. my pc, linux, mac and phone? why doesnt wifi work like that

**why:** [[WiFi]]

## wifi was designed as a cable replacement, not as a mesh

802.11 arrived in 1997 modelling the access point as an ethernet hub with the wire removed, so stations associate to the [[router]] and every frame passes through it. two laptops sitting next to each other on the same network still send packets up to the access point and back down again. that is the architecture rather than an oversight, because the access point is what holds the association state, the security context and the buffering for clients that are asleep. [[Zigbee Home Automation]] started from the opposite premise, hundreds of cheap nodes with no infrastructure present, so relaying is the baseline rather than something bolted on afterwards.

## airtime economics make relaying expensive on wifi and cheap on zigbee

a wifi radio is half-duplex on a single channel, so a relay has to receive a frame and then retransmit it, which roughly halves throughput on every hop and makes the hops interfere with each other. zigbee absorbs that cost easily, because 250 kbps carrying twenty-byte sensor payloads survives three hops with room to spare. wifi users expect hundreds of megabits, so the same per-hop tax is intolerable, and consumer [[mesh Wi-Fi]] kits sidestep it by dedicating an entire extra radio to backhaul, which is a hardware answer rather than a protocol one. a [[Wi-Fi extender]] is the degenerate case of the same problem, one hop on one radio, halving the bandwidth of everything behind it.

## power and churn rule out phones and laptops as relays

zigbee routers are mains-powered, sip milliwatts, stay in one place and relay indefinitely, which is what lets a self-healing mesh hold its shape. a phone sleeps its radio aggressively, roams between access points and then leaves the building, so any route passing through it breaks several times an hour. the devices you would most want in a home wifi mesh are exactly the ones least suited to being in one.

## four wifi mesh standards exist and each one is missing a platform

- **802.11s:** a real mesh BSS with [HWMP routing](https://en.wikipedia.org/wiki/IEEE_802.11s) written into the spec, implemented well on linux through mac80211, absent on macos and windows and out of reach on stock android, so in practice it is linux-to-linux only
- **wi-fi direct:** one device becomes a soft access point, supported on windows, android and linux through wpa_supplicant, but not on [[Mac]], which runs apple's proprietary [AWDL](https://owlink.org/) behind airdrop and sidecar instead and does not interoperate with it
- **wi-fi aware:** the closest in spirit to zigbee, since devices discover and cluster with no infrastructure at all, solid on [[Android]] and close to nonexistent on the desktop operating systems
- **IBSS ad-hoc mode:** the original peer-to-peer mode, now effectively dead, with no WPA3 support and poor driver coverage

every option is missing at least one of the four devices, and macos is the one that breaks almost all of them. a cross-platform radio mesh is therefore blocked on vendor support rather than on physics, which is why it has stayed out of reach for two decades despite the standards being finished.

## an overlay mesh delivers the useful half of this on all four devices

the property actually worth having is mutual addressability, every device reachable from every other by a stable name regardless of which network it happens to be sitting on, and that lives at layer 3 where the operating systems all cooperate.

- **tailscale:** [wireguard](https://www.wireguard.com/) underneath, first-party clients on windows, linux, macos, ios and android, NAT traversal so peers connect directly where they can and fall back to relays where they cannot, and a stable IP plus DNS name per device, already used in the vault for [[Tailscale + Home Assistant]]
- **headscale:** [the same coordination protocol self-hosted](https://github.com/juanfont/headscale), for keeping the control plane in the [[homelab]] rather than depending on tailscale's servers
- **yggdrasil:** [fully decentralised with no coordination server at all](https://yggdrasil-network.github.io/), peers finding each other over link-local multicast and routing through one another automatically, which is the genuinely zigbee-shaped option and the one that keeps working with the internet unplugged
- **zerotier:** [layer-2 emulation](https://www.zerotier.com/), worth the extra complexity only when broadcast and discovery protocols need to cross sites

none of these give back the radio property, devices extending each other's range by relaying over the air, and that one is not coming to a mixed fleet of consumer hardware. indoors it was never the part that mattered, because all four devices already sit inside range of the same access point. the mesh that was actually wanted here is the addressing, not the relaying.

## the low-power mesh world moved from zigbee to thread

[[Thread devices]] run the same 802.15.4 radio as zigbee but carry IPv6 over 6LoWPAN, so a mesh node is an addressable internet host rather than something living behind a protocol translator, and [[Matter]] is the application layer sitting on top of it. that is the closest any shipping technology gets to the original question, a real radio mesh where every device is directly addressable, and general-purpose computers are still not invited, because a pc carries no 802.15.4 radio and a phone only carries one on recent apple hardware.
