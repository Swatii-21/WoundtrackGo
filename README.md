# WoundTrack – AI-Powered Wound Monitoring System

WoundTrack is a Streamlit-based wound monitoring application that integrates three machine learning models, a SQLite digital twin, and a rule-based progression engine to support wound assessment and longitudinal tracking.

## Features

- **Wound Boundary Detection:** Identifies wound regions and estimates wound area.
- **Tissue Classification:** Analyzes wound tissue into Granulation, Fibrin, and Callus.
- **Severity Assessment:** Predicts severity grades for diabetic foot ulcers (DFU).
- **Digital Twin:** Stores patient information, wound visits, measurements, and analysis results in a local SQLite database.
- **Progression Tracking:** Applies rule-based logic to evaluate changes across patient visits.
- **AI Analysis:** Displays wound segmentation, tissue composition, severity predictions, and associated warnings.
- **Demo Mode:** Allows the application to run without trained model dependencies or available checkpoints.

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Swatii-21/WoundtrackGo.git
cd WoundtrackGo
```

### 2. Switch to the Feature Branch

To access the integrated WoundTrack implementation, switch to:

```bash
git fetch origin
git checkout feature/woundtrack-integration
```

Make sure you are on the correct branch before proceeding.

### 3. Set Up a Virtual Environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

Upgrade pip and install the project dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-models.txt
```

The `requirements-models.txt` file contains additional dependencies required for machine learning inference.

Without the model dependencies or trained checkpoints, the application may run in labelled DEMO MODE instead of using the actual models.

### 5. Download Trained Model Checkpoints

The trained model checkpoints are managed using Git Large File Storage (Git LFS).

Install and initialize Git LFS:

```bash
git lfs install
```

Download the actual model checkpoint files:

```bash
git lfs pull
```

The following model files should be available:

```text
weights/
├── boundary/
│   └── boundary_model_final_all46.pth
├── severity/
│   ├── severity_final.pt
│   └── severity_final_meta.json
└── tissue/
    ├── best_supervised.pt
    ├── sup_ctrl.pt
    └── sup_lovasz.pt
```

**Note:** The trained checkpoints are required for real model inference. If the models cannot be loaded, the application may fall back to DEMO MODE.

### 6. Run the Application

Start the Streamlit application:

```bash
python -m streamlit run app.py
```

Open the application in your browser:

```text
http://localhost:8501
```

### 7. Demo Login

The current application uses demo authentication:

- **Email:** Any email address
- **Password:** `demo123`

This is for demonstration purposes only and is not production-grade authentication.

---

## Project Structure

```text
WoundtrackGo/
│
├── app.py
│   Main Streamlit entry point and application router
│
├── config.py
│   Application colours and tissue legend configuration
│
├── backend/
│   Backend integration between the UI and ML pipeline
│   │
│   ├── service.py
│   │   Loads the WoundTrack pipeline and manages demo fallback
│   │
│   ├── twin_repository.py
│   │   Repository connecting the UI to the SQLite digital twin
│   │
│   ├── repository.py
│   ├── demo_data.py
│   ├── imaging.py
│   └── models/
│       Demo-mode model implementations
│
├── woundtrack/
│   Unified ML and digital twin backend
│   │
│   ├── segmentation.py
│   │   Model 1: Wound boundary detection and area estimation
│   │
│   ├── tissue.py
│   │   Model 2: Tissue classification ensemble
│   │
│   ├── severity.py
│   │   Model 3: DFU severity classification
│   │
│   ├── twin_db.py
│   │   SQLite digital twin and database operations
│   │
│   ├── rules.py
│   │   Rule-based wound progression assessment
│   │
│   ├── pipeline.py
│   │   Integrates model inference, database storage and rules
│   │
│   ├── config.py
│   └── utils.py
│
├── ui/
│   Streamlit user interface
│   │
│   └── pages/
│       Application pages including dashboard, analysis,
│       new visit, profile and progression tracking
│
├── tests/
│   Unit and integration tests
│
├── scripts/
│   Utility and model testing scripts
│
├── assets/
│   Application images and visual assets
│
├── weights/
│   Trained model checkpoints managed through Git LFS
│
├── requirements.txt
│   Core application dependencies
│
├── requirements-models.txt
│   Machine learning dependencies
│
├── .gitignore
├── .gitattributes
└── README.md
```

### Runtime Data

The application automatically creates the following directory when the real digital twin database is initialized:

```text
data/
├── digital_twin.db
└── visit_images/
```

- `digital_twin.db`: Stores patient records, wound visits, measurements, and analysis results.
- `visit_images/`: Stores uploaded wound images and generated analysis images.

This directory is created locally at runtime and is not included in the Git repository.

---

## How a Wound Visit Is Processed

The application follows this workflow:

1. The user registers or selects a patient.
2. The user uploads a wound image through **Add New Visit**.
3. The image is passed to `WoundTrackPipeline.process_visit()`.
4. The three models perform the relevant analysis:
   - Model 1: Wound boundary detection and area estimation.
   - Model 2: Tissue classification.
   - Model 3: Severity classification, only for patients with diabetic foot ulcers.
5. The visit information and analysis results are saved in the SQLite digital twin.
6. The rule engine evaluates the patient's visit history.
7. The results are displayed in AI Analysis and Progression Tracking.

---

## Important Notes and Limitations

- **Tissue classes:** The tissue model predicts Granulation, Fibrin, and Callus. These are not equivalent to slough or necrotic tissue classifications.
- **Severity classification:** Severity assessment is applicable only to diabetic foot ulcers (DFU). It is marked as not applicable for other wound types.
- **Wound area:** Area is calculated as a percentage of the image, not in cm². Images should be captured from a similar distance and angle when comparing visits.
- **Risk level:** Patient risk level is entered by the clinician. It is not predicted by the machine learning models.
- **Authentication:** The current login system is for demonstration purposes and does not provide real user authentication.
- **Clinical use:** Model outputs are intended for research and demonstration. They are not a substitute for professional medical assessment.

---

## Running Tests

Run the individual test scripts from the project root:

```bash
python tests/test_rules.py
python tests/test_pipeline.py
python tests/test_integration.py
```

Additional UI tests are available in:

```text
tests/test_ui.py
```

The dummy-weight utility is available at:

```text
tests/make_dummy_weights.py
```

---

## Technology Stack

- **Programming Language:** Python
- **Frontend:** Streamlit
- **Machine Learning:** PyTorch
- **Computer Vision:** OpenCV
- **Segmentation:** U-Net with ResNet encoder
- **Severity Classification:** Deep learning-based image classification
- **Database:** SQLite
- **Model Storage:** Git LFS

---

## Development Branch

The integrated WoundTrack implementation is available on:

```text
feature/woundtrack-integration
```

To get the latest version of this branch:

```bash
git pull origin feature/woundtrack-integration
```

To switch back to the main branch:

```bash
git checkout main
```

---

**WoundTrack – AI-assisted wound assessment, digital twin management, and progression monitoring.**