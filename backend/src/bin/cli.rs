use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        print_usage();
        return;
    }

    match args[1].as_str() {
        "list-backups" => {
            if args.len() < 3 {
                eprintln!("Usage: medguard-cli list-backups <file_path>");
                return;
            }
            list_backups(&args[2]);
        }
        "restore" => {
            if args.len() < 3 {
                eprintln!("Usage: medguard-cli restore <file_path> [--version <n>]");
                return;
            }
            let version = parse_version(&args);
            restore_file(&args[2], version);
        }
        "status" => {
            show_status();
        }
        _ => {
            eprintln!("Unknown command: {}", args[1]);
            print_usage();
        }
    }
}

fn print_usage() {
    println!("MedGuard CLI - Command Line Interface\n");
    println!("Usage:");
    println!("  medguard-cli list-backups <file_path>      List available backup versions");
    println!("  medguard-cli restore <file_path> [--version <n>]   Restore file from backup");
    println!("  medguard-cli status                         Show system status");
    println!("\nExamples:");
    println!("  medguard-cli list-backups test_medical_data/patient_001.dcm");
    println!("  medguard-cli restore test_medical_data/patient_001.dcm --version 5");
}

fn list_backups(file_path: &str) {
    println!("📋 Listing backups for: {}", file_path);
    println!("   (Feature requires running backend server)");
    println!("   Use REST API: GET http://localhost:8080/api/backups");
}

fn restore_file(file_path: &str, version: Option<u64>) {
    println!("🔄 Restoring file: {}", file_path);
    if let Some(v) = version {
        println!("   Version: {}", v);
    } else {
        println!("   Version: latest");
    }
    println!("   (Feature requires running backend server)");
    println!("   Use REST API: POST http://localhost:8080/api/restore");
}

fn show_status() {
    println!("📊 MedGuard System Status");
    println!("   (Feature requires running backend server)");
    println!("   Use REST API: GET http://localhost:8080/api/status");
}

fn parse_version(args: &[String]) -> Option<u64> {
    for i in 0..args.len() {
        if args[i] == "--version" && i + 1 < args.len() {
            return args[i + 1].parse().ok();
        }
    }
    None
}
