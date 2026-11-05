# Deploying the ClearTab beta (Oracle Cloud Always Free)

One small virtual machine runs three containers: Postgres, the API, and the web app behind Caddy (automatic
HTTPS). Cost: $0 on the Always Free tier. Time: about 1 hour the first time.

What lives where:
- Code: this repository (public).
- `data-server/` (never in git): `db/cleartab.sql.gz` (database dump, 2 MB) and `reference/` (CMS MUE zips and
  `ncci_ptp.sqlite`, about 240 MB; CPT codes under the AMA license, so they stay private on the server).
- `deploy/.env` (never in git): database password, Groq key, site address.

## 1. Create the VM (once)
1. Sign up at https://www.oracle.com/cloud/free/ (a card is asked for identity; Always Free resources are not
   charged). Pick a home region close to Arizona (US West, Phoenix or San Jose); it cannot be changed later.
2. Compute -> Instances -> Create instance:
   - Image: Canonical Ubuntu 24.04.
   - Shape: Ampere `VM.Standard.A1.Flex`, 2 OCPU, 12 GB memory (Always Free allows up to 4 OCPU / 24 GB in total).
     If it says "out of capacity", try another availability domain or try again later;
     `VM.Standard.E2.1.Micro` (1 GB) is a fallback but tight.
   - Networking: public subnet, assign a public IPv4 address.
   - SSH keys: upload your public key (`~/.ssh/id_ed25519.pub`; create one with `ssh-keygen -t ed25519`).
3. Open ports 80 and 443:
   - Networking -> Virtual cloud networks -> your VCN -> Security lists -> Default -> Add ingress rules:
     source `0.0.0.0/0`, TCP, destination port 80; the same for 443.
   - On the VM itself (Oracle's Ubuntu image blocks ports with iptables):
     ```
     sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
     sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
     sudo netfilter-persistent save
     ```

## 2. Install Docker on the VM (once)
```
ssh ubuntu@<server-ip>
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu && exit     # log in again so the group applies
```

## 3. Copy code and data
On the VM:
```
git clone https://github.com/MrazzKa/cleartab.git ~/cleartab
cd ~/cleartab && git checkout main          # or the branch being deployed
cp deploy/.env.example deploy/.env && nano deploy/.env   # strong POSTGRES_PASSWORD, GROQ_API_KEY
```
On the machine with the loaded database (WSL):
```
./deploy/prepare_data.sh
scp -r data-server ubuntu@<server-ip>:~/cleartab/
```

## 4. Start
On the VM:
```
cd ~/cleartab
docker compose -f deploy/compose.yml --env-file deploy/.env up -d --build
docker compose -f deploy/compose.yml --env-file deploy/.env ps
curl -s localhost/api/plans
```
Open `http://<server-ip>/` in a browser. The database is restored from the dump on the first start only.

## 5. HTTPS and an address
Camera access for scanning and "Add to home screen" need HTTPS, so a name is required:
- Free: a DuckDNS name (https://www.duckdns.org, sign in, create `cleartab-xyz`, point it at the server IP), or
  `<server-ip-with-dashes>.sslip.io`, which needs no sign-up (for example `129-146-1-2.sslip.io`).
- Paid: any domain with an A record pointing at the server IP.
Set `SITE_ADDRESS=<that name>` in `deploy/.env` and run `up -d` again. Caddy gets the certificate by itself.

## Updating
```
cd ~/cleartab && git pull
docker compose -f deploy/compose.yml --env-file deploy/.env up -d --build
```
New database content: run `prepare_data.sh` again, copy `data-server/db`, then
`docker compose -f deploy/compose.yml --env-file deploy/.env down -v` (this deletes the old database volume)
and `up -d`.

## Limits and privacy on the public server
- Document reading is limited per visitor (6 per hour, 15 per day) and in total (150 per day) so the free model
  quota is not used up; change the numbers in `deploy/.env`. Typing amounts always works.
- No access logs are kept by Caddy or uvicorn; the API logs the path and status only, never query strings,
  bodies or addresses. Photos are passed to the reading service for one request and not stored.
- Back up nothing personal: there is nothing personal on the server.

## Test locally first (optional)
```
./deploy/prepare_data.sh
printf 'POSTGRES_PASSWORD=test\nGROQ_API_KEY=\nHTTP_PORT=8099\nHTTPS_PORT=8443\n' > /tmp/deploy.env
docker compose -p cleartab-beta -f deploy/compose.yml --env-file /tmp/deploy.env up -d --build
# http://localhost:8099/ ; stop with: docker compose -p cleartab-beta -f deploy/compose.yml --env-file /tmp/deploy.env down -v
```
