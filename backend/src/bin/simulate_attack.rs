use std::fs;
use std::io::Write;
use std::thread;
use std::time::Duration;
use rand::Rng;

fn main() {
    println!("⚠️  RANSOMWARE SIMULATION (SAFE - Test Environment Only)");
    println!("This will simulate ransomware behavior on test files only.");
    println!("MedGuard should detect and prevent this attack.\n");

    thread::sleep(Duration::from_secs(2));

    println!("🔍 Phase 1: Reconnaissance - Reading files...");
    thread::sleep(Duration::from_millis(500));

    let test_dir = "test_medical_data";
    if !std::path::Path::new(test_dir).exists() {
        eprintln!("❌ Error: test_medical_data directory not found!");
        eprintln!("   Run 'cargo run --bin generate_test_data' first.");
        return;
    }

    // Read directory
    let entries: Vec<_> = fs::read_dir(test_dir)
        .expect("Failed to read directory")
        .filter_map(|e| e.ok())
        .collect();

    println!("✓ Found {} files to encrypt\n", entries.len());

    println!("🔥 Phase 2: Rapid File Encryption Attack...");
    thread::sleep(Duration::from_millis(500));

    let mut rng = rand::thread_rng();
    
    // Simulate rapid file modification (ransomware behavior)
    for (i, entry) in entries.iter().enumerate() {
        let path = entry.path();
        
        if let Some(ext) = path.extension() {
            if ext == "dcm" || ext == "hl7" || ext == "xml" {
                println!("   Encrypting: {:?}", path.file_name().unwrap());
                
                // Read original file
                if let Ok(original_data) = fs::read(&path) {
                    // Simulate encryption by writing random data (HIGH ENTROPY)
                    let random_data: Vec<u8> = (0..original_data.len())
                        .map(|_| rng.gen())
                        .collect();
                    
                    // Write "encrypted" data
                    if let Ok(mut file) = fs::File::create(&path) {
                        let _ = file.write_all(&random_data);
                    }
                    
                    // Ransomware typically operates very quickly
                    thread::sleep(Duration::from_millis(50));
                }
            }
        }
        
        if i == 5 {
            println!("\n   ⚠️  MedGuard should detect the attack around here...");
            thread::sleep(Duration::from_secs(1));
        }
    }

    println!("\n🔥 Phase 3: Attempting to add ransomware extensions...");
    thread::sleep(Duration::from_millis(500));

    // Try to rename files with suspicious extensions
    for entry in entries.iter().take(3) {
        let path = entry.path();
        let locked_path = path.with_extension("locked");
        
        println!("   Renaming: {:?} -> {:?}", 
                 path.file_name().unwrap(), 
                 locked_path.file_name().unwrap());
        
        let _ = fs::rename(&path, &locked_path);
        thread::sleep(Duration::from_millis(100));
    }

    println!("\n💀 Phase 4: Simulating ransom note creation...");
    thread::sleep(Duration::from_millis(500));

    let ransom_note = format!(
        "{}/_RANSOM_NOTE.txt",
        test_dir
    );

    if let Ok(mut file) = fs::File::create(&ransom_note) {
        let note = "\
===========================================
   YOUR FILES HAVE BEEN ENCRYPTED!
===========================================

All your medical data has been encrypted.
To recover your files, you must pay 10 BTC.

This is a TEST SIMULATION.
MedGuard should have detected this attack.
===========================================
";
        let _ = file.write_all(note.as_bytes());
        println!("✓ Created ransom note");
    }

    println!("\n📊 Attack Simulation Complete!");
    println!("\n🛡️  Check MedGuard Dashboard:");
    println!("   - Threat alerts should be visible");
    println!("   - High threat score (70+)");
    println!("   - Automatic backups should be available");
    println!("   - Files can be restored from backups");
    println!("\n⚠️  Note: This was a SAFE simulation on test data only.");
}
