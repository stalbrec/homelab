# Data handling

```mermaid
graph LR

subgraph hetznerShare[Nextcloud@hetzner]
usera[User A]:::component
userb[User B]:::component
docsprod["shared Documents directory"]:::component
usera <--> docsprod
userb <--> docsprod
end
hetznerShare:::region



subgraph TrueNAS["TrueNAS@Home"]
docsTrueNAS[Documents backup]:::component
useraTrueNAS["User A"]:::component
userbTrueNAS["User B"]:::component
end
TrueNAS:::region

subgraph manitu[Nextcloud@manitu]
docsManitu[Documents backup]:::component

end
manitu:::region

docsprod -->|cloud sync| docsTrueNAS
docsTrueNAS -->|cloud sync| docsManitu

TrueNAS --->|rsync via ssh| hetznerBox

subgraph hetznerBox[StorageBox@hetzner\n<small>1-to-1 mirror of User directoriesTrueNAS</small>]
docsManitu[Documents backup]:::component

end
hetznerBox:::region


clientA1[PC/Phone User A]:::user
clientA1 <-->|Nextcloud Client| usera
clientA1 <-->|Samba share| TrueNAS
clientB1[PC/Phone User B]:::user
clientB1 <-->|Nextcloud Client| userb
clientB1 <-->|Samba share| TrueNAS



classDef region fill:#ffffff, color:black, stroke-width:4, stroke:black
classDef component fill:#fbb4ae, stroke-width:0
classDef user color:black, fill:#ccebc5, stroke:black

```
