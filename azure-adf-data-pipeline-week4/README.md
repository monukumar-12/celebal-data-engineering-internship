# Azure Cloud Fundamentals and Data Pipeline using Azure Data Factory

## Objective

The objective of this assignment is to understand Azure cloud fundamentals and build an end-to-end data pipeline using Azure Storage Account and Azure Data Factory (ADF).

---

## Technologies Used

* Microsoft Azure
* Azure Resource Group
* Azure Storage Account
* Azure Blob Storage
* Azure Data Factory (ADF)
* Azure IAM (Access Control)
* CSV Dataset (Sample Superstore)

---

## Project Workflow

```text
Sample-Superstore.csv
        │
        ▼
Azure Blob Storage (Input Container)
        │
        ▼
Get Metadata Activity
        │
        ▼
Copy Data Activity
        │
        ▼
Azure Blob Storage (Output Container)
```

---

## Assignment Tasks

### Task 1 – Resource Group

* Created an Azure Resource Group to organize all project resources.

### Task 2 – Storage Setup

* Created an Azure Storage Account.
* Created Blob Storage containers.
* Uploaded the **Sample Superstore** CSV dataset.

### Task 3 – Azure Data Factory

* Created Azure Data Factory.
* Configured a Linked Service with Azure Blob Storage.
* Created source and destination datasets.
* Used the **Get Metadata** activity to validate the source file.

### Task 4 – Pipeline Development

* Created a pipeline using the **Copy Data** activity.
* Configured the source and destination datasets.
* Connected the activities to build the data pipeline.

### Task 5 – Pipeline Execution

* Executed the pipeline using **Debug/Trigger**.
* Verified successful pipeline execution.

### Task 6 – IAM Roles

* Assigned the required IAM roles:

  * Reader
  * Contributor
* Configured Azure Data Factory access to the Storage Account.

---

## Dataset

* **Dataset:** Sample Superstore
* **Format:** CSV
* **Location:** `dataset/Sample-Superstore.csv`

---

## Repository Structure

```text
azure-adf-data-pipeline-week4/
│── README.md
│
├── dataset/
│   └── Sample-Superstore.csv
│
└── screenshots/
    ├── 01-resource-group.png
    ├── 02-storage-account.png
    ├── 03-blob-container.png
    ├── 04-linked-service.png
    ├── 05-source-dataset.png
    ├── 06-destination-dataset.png
    ├── 07-get-metadata.png
    ├── 08-pipeline-design.png
    ├── 09-pipeline-execution.png
    ├── 10-output-container.png
    └── 11-role-assignment.png
```

---

## Screenshots

The `screenshots` folder contains screenshots of:

* Resource Group
* Storage Account
* Blob Container with uploaded CSV
* Linked Service
* Source Dataset
* Destination Dataset
* Get Metadata Activity
* Pipeline Design
* Pipeline Execution (Succeeded)
* Output Container
* IAM Role Assignment

---

## Learning Outcomes

* Understood Azure cloud fundamentals.
* Created and managed Azure Storage resources.
* Connected Azure Blob Storage with Azure Data Factory.
* Built and executed an end-to-end data pipeline.
* Retrieved file metadata using the **Get Metadata** activity.
* Copied data between Blob Storage containers using the **Copy Data** activity.
* Configured IAM roles for secure resource access.

---

## Conclusion

This project demonstrates the implementation of a complete Azure Data Factory pipeline that reads a CSV file from Azure Blob Storage, validates the file using the **Get Metadata** activity, copies the data to a destination container, and verifies successful execution while following Azure cloud best practices.
