
CREATE DATABASE petcare;
USE petcare;
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(50),
    password VARCHAR(255) NOT NULL, -- hashed password
    email VARCHAR(100) UNIQUE,
    role ENUM('Admin','Veterinarian','Pet Owner') NOT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    vchr_status ENUM('A', 'D') DEFAULT 'A',  -- A - alive user D - Deleted user
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE owners (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    phone VARCHAR(20),
    address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE pets (
    pet_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT,
    name VARCHAR(50),
    breed VARCHAR(50),
    age INT,
    gender ENUM('Male','Female'),
    medical_history TEXT,
    image text DEFAULT "",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id)
);
CREATE TABLE veterinarians (
    vet_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    specialization VARCHAR(100),
    phone VARCHAR(20),
    clinic_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT,
    owner_id INT,
    vet_id INT,
    appointment_date DATETIME,
    status ENUM('Pending','Confirmed','Completed','Cancelled') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id),
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id),
    FOREIGN KEY (vet_id) REFERENCES users(user_id)
);
CREATE TABLE vaccinations (
    vaccination_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT,
    vet_id INT,
    vaccine_name VARCHAR(100),
    date_given DATE,
    next_due_date DATE,
    notes TEXT,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id),
    FOREIGN KEY (vet_id) REFERENCES veterinarians(vet_id)
);
CREATE TABLE medications (
    medication_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT,
    vet_id INT,
    medicine_name VARCHAR(100),
    dosage VARCHAR(50),
    start_date DATE,
    end_date DATE,
    notes TEXT,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id),
    FOREIGN KEY (vet_id) REFERENCES veterinarians(vet_id)
);
CREATE TABLE expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT,
    pet_id INT,
    description VARCHAR(100),
    amount DECIMAL(10,2),
    date DATE,
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id),
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id)
);

describe users;
describe owners;
describe pets;
describe appointments;
describe expenses;
describe medications;
describe vaccinations;
describe veterinarians;