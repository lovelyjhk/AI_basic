use std::fs;
use std::io::Write;
use rand::Rng;

fn main() {
    println!("🏥 Generating test medical data...");

    // Create test directory
    fs::create_dir_all("test_medical_data").expect("Failed to create directory");

    // Generate DICOM-like files
    for i in 1..=10 {
        let filename = format!("test_medical_data/patient_{:03}.dcm", i);
        let mut file = fs::File::create(&filename).expect("Failed to create file");
        
        // DICOM files contain medical imaging data - simulate with structured data
        let header = format!("DICM_HEADER_PATIENT_{:03}\n", i);
        file.write_all(header.as_bytes()).unwrap();
        
        // Add some medical-like data
        let data = format!(
            "Patient ID: P{:03}\n\
             Study Date: 2025-10-01\n\
             Modality: CT\n\
             Image Data: ",
            i
        );
        file.write_all(data.as_bytes()).unwrap();
        
        // Add some binary-like data (low entropy - typical of medical images)
        let image_data = vec![128u8; 1024 * 10]; // 10KB of simulated grayscale data
        file.write_all(&image_data).unwrap();
        
        println!("✓ Created: {}", filename);
    }

    // Generate HL7 message files
    for i in 1..=5 {
        let filename = format!("test_medical_data/lab_result_{:03}.hl7", i);
        let mut file = fs::File::create(&filename).expect("Failed to create file");
        
        let hl7_message = format!(
            "MSH|^~\\&|LAB|Hospital|EHR|Clinic|20251001120000||ORU^R01|MSG{:03}|P|2.5\n\
             PID|1||P{:03}||Doe^John||19800101|M\n\
             OBR|1||LAB{:03}|CBC^Complete Blood Count\n\
             OBX|1|NM|WBC^White Blood Cell Count||7.5|10^9/L|4.5-11.0|N|||F\n\
             OBX|2|NM|RBC^Red Blood Cell Count||4.8|10^12/L|4.5-5.5|N|||F\n",
            i, i, i
        );
        
        file.write_all(hl7_message.as_bytes()).unwrap();
        println!("✓ Created: {}", filename);
    }

    // Generate EHR XML files
    for i in 1..=5 {
        let filename = format!("test_medical_data/ehr_record_{:03}.xml", i);
        let mut file = fs::File::create(&filename).expect("Failed to create file");
        
        let xml_content = format!(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
             <EHR>\n\
               <PatientID>P{:03}</PatientID>\n\
               <Name>John Doe</Name>\n\
               <DateOfBirth>1980-01-01</DateOfBirth>\n\
               <Gender>Male</Gender>\n\
               <Encounter>\n\
                 <Date>2025-10-01</Date>\n\
                 <Type>Outpatient</Type>\n\
                 <ChiefComplaint>Routine checkup</ChiefComplaint>\n\
                 <Diagnosis>Healthy</Diagnosis>\n\
                 <Medications>\n\
                   <Medication>None</Medication>\n\
                 </Medications>\n\
               </Encounter>\n\
             </EHR>\n",
            i
        );
        
        file.write_all(xml_content.as_bytes()).unwrap();
        println!("✓ Created: {}", filename);
    }

    println!("\n✅ Test medical data generated successfully!");
    println!("📁 Location: ./test_medical_data/");
    println!("   - 10 DICOM files (.dcm)");
    println!("   - 5 HL7 messages (.hl7)");
    println!("   - 5 EHR records (.xml)");
}
