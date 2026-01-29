
https://desec.io is excellent.

Free, no ads, no premium accounts, no nag emails, run by a non-profit based in germany. iirc the domain limit is 15 but if you ask nicely they might increase it for you if youre a heavy user. The control panel works well and offers everything i need, they have a API of course and its compatible with Lets Encrypt with the typical setups (Traefik, lego, Caddy with a plugin etc).

They also offer free subdomains like example.dedyn.io which can be managed through the same panel. Or you already have a domain somewhere else, then change the nameservers to dedyn and you can manage "full" domains and the free subdomain under one panel all together.

And copy/pasting a older comment from here of mine:

https://nic.eu.org gives out free domains in the format of example.eu.org

Yes those are "real domains", not "subdomains" of eu.org as it may appear.

- .eu.org is a "public suffix" like .co.uk or .com.au etc.

- These are not a "scam" like Freenom or similar things. The big differences are:

- eu.org is their own registry, nobody is taken these domains and control away from them.

- They are a non-profit organization. You get no ads, no spam, nothing.

- You are the rightful owner of the domain, you have full control over it.

- You do not need to be a resident of the EU or anything, or provide any such proof.

- You do need to provide a name and address when signing up, but you could provide a fake address if you want, see below.

- You can select to keep the provided address out of the public whois information (often called a privacy option or similar). So you can provide a real name and address if you want to. If you chose to supply fake information, keep in mind that if there ever is a issue about the legal ownership of the domain, you might be in a tough spot to proof that you are that fake person... For typical homelab/selfhosting usage, this probably doesnt matter.

- You can, and should, have nameservers running somewhere and supply them to nic.eu.org. To keep it free i recommend using deSEC.io which works perfectly well with them, including DNSSEC. deSEC are also a non-profit, no ads or personal data collection etc. and strict data protection laws because they are based in germany. You can have up to 15 domains under one account. There are no paid accounts or anything. In case you need more than 15 domains, you could probably use multiple accounts, or simply contact them and they are happy to increase your limit, for free.

**The only actual downside** to eu.org is because they are just a simple non-profit service, their validation process for new domain signups appears to be done manually, which means it usually **takes a few days but even up to two weeks**. Just be patient and wait for an email to notify you of acceptance. Once that is done they provide no real support, you have full access to the domain settings through the panel at nic.eu.org when you log in. Any changes you make are automated and there are no manual wait times etc after the initial wait.

Personally i am running around 20 of these domains by now, most of them under deSEC and its working perfectly. The initial wait is of course annoying, but thats a one-time thing only. I had a few that were granted within a day, some after two weeks, most of them were around a week. Since none of these are time-sensitive for me, i am more than happy to "pay that as the price" for receiving full control and a very stable and reliable service.

**TL;DR If you are a complete beginner with all of selfhosting etc, it might be better to spend money on some things to actually receive support. But if you either are experienced enough, or you want to learn and tinker, this is a great and really free alternative.**

If you are fine with using subdomains, people have already mentioned DuckDNS.org which has become some kind of classic i guess. They are working perfectly fine, no real issues. As a alternative i can, again, recommend deSEC.io, they also provide free subdomains in the format of example.dedyn.io and you can manage the DNS very nicely through their control panel. iirc DuckDNS has a limit of 5 per account, deSEC has a limit of 15 per account. In case you want to run a [[dynamic DNS]] (DDNS) with a dynamic home IP for example, both of them support that and tools like **ddclient** are compatible to automatically update the DNS when the IP changes. Both DuckDNS and deSEC provide publicsuffixes with their .duckdns.org and .dedyn.io

[[Web hosting]]
[[free hosting]]
[[open source]]