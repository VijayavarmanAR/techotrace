# **Cyber Forensics Toolkit**

## **Overview**
The **Cyber Forensics Toolkit** is a forensic analysis tool that helps security analysts identify vulnerabilities in files, networks, logs, and registries. The tool supports forensic image formats like **RAW, SMART, and E01** for detailed investigation.

## **Features**
- **File Analysis**: Scan uploaded forensic image files to detect suspicious files.
- **Network Analysis**: Identify network vulnerabilities and anomalies.
- **Log Analysis**: Parse and analyze logs to detect potential security breaches.
- **Registry Analysis**: Examine registry entries to uncover signs of system compromise.

## **Technologies Used**
- **Backend**: Python (Django/Flask)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite / PostgreSQL (optional)
- **Libraries & Tools**:
  - `scapy` (Network analysis)
  - `pandas` (Log analysis)
  - `pytsk3` (File system forensics)
  - `python-registry` (Windows Registry forensics)
  - `dfvfs` (Digital Forensics Virtual File System for image parsing)

## **Installation**
### **1. Clone the Repository**
```bash
git clone https://github.com/VijayavarmanAR/techotrace.git
cd techotrace
```

### **2. Set Up a Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate     # For Windows
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Set Up Database**
```bash
python manage.py migrate
```

### **5. Run the Application**
```bash
python manage.py runserver
```
Access the application at **http://127.0.0.1:8000/**.

---

## **Usage**
1. **Upload a forensic image** (`.raw`, `.smart`, `.e01`).
2. **Select the analysis module** (File, Network, Log, or Registry).
3. **View vulnerability reports** generated by the system.
4. **Export results** for further examination.

---

## **Project Structure**
```
cyber-forensics-toolkit/
│── backend/
│   ├── file_analysis.py
│   ├── network_analysis.py
│   ├── log_analysis.py
│   ├── registry_analysis.py
│   ├── utils/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│── frontend/
│   ├── static/
│   ├── templates/
│   ├── index.html
│── requirements.txt
│── manage.py
│── README.md
```

---

## **Endpoints**
| Endpoint           | Method | Description |
|--------------------|--------|-------------|
| `/upload/`        | POST   | Upload forensic image file |
| `/file-analysis/` | GET    | Analyze files for threats |
| `/network/`       | GET    | Perform network vulnerability assessment |
| `/logs/`          | GET    | Scan system logs for anomalies |
| `/registry/`      | GET    | Extract and analyze registry information |
