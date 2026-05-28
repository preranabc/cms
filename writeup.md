# Article CMS – Azure Deployment Write-Up

## Resource Justification: VM vs. App Service

### Virtual Machine (VM) Analysis

**Cost:**  
A Standard B1ls VM (~$3–5/month) is one of the cheapest compute options on Azure. However, the true cost is higher when you factor in management time: patching the OS, managing NGINX, configuring SSL manually, and handling uptime. For a development project this is acceptable, but for production it adds hidden operational costs.

**Scalability:**  
VMs require manual effort to scale. You must either resize the VM (vertical scaling) or configure a Virtual Machine Scale Set (horizontal scaling), both of which involve significant setup. There is no built-in auto-scale for a standalone VM. This makes it unsuitable if you expect traffic spikes.

**Availability:**  
A single VM has no automatic failover. If the VM crashes or needs rebooting (e.g., for OS patches), the app goes down. To achieve high availability, you need to configure Availability Sets or Zones, which increases complexity and cost.

**Workflow:**  
Deployment on a VM is entirely manual — SSH in, git pull, restart the app. Every dependency (Python, NGINX, ODBC drivers) must be installed manually. This increases deployment time and risk of human error compared to managed services.

---

### App Service Analysis

**Cost:**  
The Free F1 plan is $0/month, which makes it ideal for learning and development. The B1 paid tier (~$13/month) is still significantly cheaper than managing a VM when you account for the time saved on infrastructure management.

**Scalability:**  
App Service supports built-in auto-scaling. You can configure rules to add instances based on CPU or memory usage without any infrastructure changes. Scale-out is handled by Azure automatically. This makes App Service far more production-ready.

**Availability:**  
App Service comes with a built-in SLA of 99.95% uptime (on Basic tier and above). Azure handles OS patching, hardware failures, and automatic restarts — all without downtime for your application.

**Workflow:**  
Deployment via GitHub Actions (Deployment Center) means every push to your repo automatically builds and deploys the app. Environment variables are managed through Azure's Application Settings UI, keeping secrets out of code. This is a significantly faster and safer workflow.

---

## Decision: App Service

**I chose Azure App Service** for deploying this CMS application. The key reasons are:

1. **Zero infrastructure management:** App Service abstracts away the OS, web server, and runtime entirely. There is no need to configure NGINX, set up SSL manually, or manage system packages — all of which are time-consuming on a Windows development machine where Linux tools are unavailable.

2. **Integrated CI/CD:** The Deployment Center's GitHub integration means the app is automatically deployed on every commit, which is the industry-standard workflow for web apps and far more reliable than manual SSH-based deployments.

3. **Cost-effective for development:** The Free F1 plan costs nothing, which is appropriate for a student/portfolio project. When the app needs to go to production, upgrading to a paid tier takes one click, with no re-configuration required.

---

## App Changes That Would Prompt Switching to a VM

If the application requirements changed in any of the following ways, I would reconsider using a VM or a container-based solution:

1. **Custom runtime or system-level dependencies:** If the app required a specific ODBC version, a binary compiled from source, GPU access, or a non-Python process running alongside it (e.g., a background worker using a tool not available on App Service), a VM would be necessary since App Service restricts low-level OS access.

2. **Full control over networking and security:** If the project required placing the app inside a private VNet with custom firewall rules, using a custom domain with your own CA-signed certificate at the OS level, or integrating with on-premises infrastructure via VPN, a VM gives the full control that App Service cannot.

3. **Stateful file system requirements:** App Service has an ephemeral file system — any files written to disk are lost on restart. If the app needed persistent local storage beyond what Azure Blob provides (e.g., a local SQLite cache, file-based session storage), a VM with a persistent disk would be required.

To accommodate these changes, I would need to: configure a Virtual Network, provision managed disks, set up NGINX as a reverse proxy, configure systemd to keep the Flask process running, and implement a CI/CD pipeline (e.g., GitHub Actions SSH deployment) to replace the App Service Deployment Center.
