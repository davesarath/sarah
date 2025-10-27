-- =====================================================
-- PET CARE MANAGEMENT SYSTEM DATABASE SETUP
-- =====================================================
-- This file creates all the tables needed for the pet care system
-- Run this file in MySQL to set up the complete database structure

-- Create the main database for our pet care system
CREATE DATABASE petcare;
USE petcare;

-- =====================================================
-- USERS TABLE - Main table for all system users
-- =====================================================
-- This table stores basic information for all users (Admin, Vets, Pet Owners)
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID for each user (auto-generated)
    full_name VARCHAR(50),                   -- User's full name (up to 50 characters)
    password VARCHAR(255) NOT NULL,          -- Hashed password (never store plain text!)
    email VARCHAR(100) UNIQUE,               -- Email address (must be unique across all users)
    role ENUM('Admin','Veterinarian','Pet Owner') NOT NULL,  -- What type of user they are
    status ENUM('Active', 'Inactive') DEFAULT 'Active',      -- Whether account is active
    vchr_status ENUM('A', 'D') DEFAULT 'A',  -- A = Alive (active), D = Deleted (soft delete)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP           -- When account was created
);
-- =====================================================
-- OWNERS TABLE - Additional info for Pet Owner users
-- =====================================================
-- This table stores extra information specific to pet owners
-- It's linked to the users table (one user can be one owner)
CREATE TABLE owners (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID for each pet owner
    user_id INT,                              -- Links to users table (which user this owner is)
    phone VARCHAR(20),                        -- Owner's phone number
    address TEXT,                             -- Owner's home address
    FOREIGN KEY (user_id) REFERENCES users(user_id)  -- Ensures user_id exists in users table
);
-- =====================================================
-- PETS TABLE - Information about all pets in the system
-- =====================================================
-- This table stores all pet information and links each pet to their owner
CREATE TABLE pets (
    pet_id INT AUTO_INCREMENT PRIMARY KEY,    -- Unique ID for each pet
    owner_id INT,                             -- Which owner owns this pet (links to owners table)
    name VARCHAR(50),                         -- Pet's name (e.g., "Fluffy", "Max")
    breed VARCHAR(50),                        -- Pet's breed (e.g., "Golden Retriever", "Persian Cat")
    age INT,                                  -- Pet's age in years
    gender ENUM('Male','Female'),             -- Pet's gender (only Male or Female allowed)
    medical_history TEXT,                     -- Any existing medical conditions or history
    image TEXT DEFAULT "",                   -- Path to pet's photo (stored as file path)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When pet was added to system
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id)  -- Ensures owner_id exists in owners table
);
-- =====================================================
-- VETERINARIANS TABLE - Additional info for Veterinarian users
-- =====================================================
-- This table stores extra information specific to veterinarians
-- It's linked to the users table (one user can be one veterinarian)
CREATE TABLE veterinarians (
    vet_id INT AUTO_INCREMENT PRIMARY KEY,    -- Unique ID for each veterinarian
    user_id INT,                              -- Links to users table (which user this vet is)
    specialization VARCHAR(100),              -- Vet's specialty (e.g., "Small Animals", "Surgery")
    phone VARCHAR(20),                        -- Vet's phone number
    clinic_address TEXT,                      -- Address of vet's clinic
    FOREIGN KEY (user_id) REFERENCES users(user_id)  -- Ensures user_id exists in users table
);
-- =====================================================
-- APPOINTMENTS TABLE - Scheduling system for vet visits
-- =====================================================
-- This table manages all appointments between pet owners and veterinarians
-- It connects pets, owners, and vets together for scheduled visits
CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID for each appointment
    pet_id INT,                                     -- Which pet the appointment is for
    owner_id INT,                                   -- Which owner is booking the appointment
    vet_id INT,                                     -- Which veterinarian will see the pet
    appointment_date DATETIME,                      -- Date and time of appointment
    status ENUM('Pending','Confirmed','Completed','Cancelled') DEFAULT 'Pending',  -- Appointment status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When appointment was booked
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id),      -- Ensures pet exists
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id), -- Ensures owner exists
    FOREIGN KEY (vet_id) REFERENCES users(user_id)      -- Links to vet's user account
);
-- =====================================================
-- VACCINATIONS TABLE - Record of all pet vaccinations
-- =====================================================
-- This table tracks all vaccinations given to pets by veterinarians
-- Helps keep track of vaccination schedules and due dates
CREATE TABLE vaccinations (
    vaccination_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID for each vaccination record
    pet_id INT,                                     -- Which pet received the vaccination
    vet_id INT,                                     -- Which vet administered the vaccination
    vaccine_name VARCHAR(100),                      -- Name of vaccine (e.g., "Rabies", "DHPP")
    date_given DATE,                                -- When the vaccination was given
    next_due_date DATE,                             -- When the next dose is due (optional)
    notes TEXT,                                     -- Any additional notes about the vaccination
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id),           -- Ensures pet exists
    FOREIGN KEY (vet_id) REFERENCES veterinarians(vet_id)   -- Ensures vet exists
);
-- =====================================================
-- MEDICATIONS TABLE - Record of all pet medications
-- =====================================================
-- This table tracks all medications prescribed to pets by veterinarians
-- Helps monitor treatment plans and medication schedules
CREATE TABLE medications (
    medication_id INT AUTO_INCREMENT PRIMARY KEY,   -- Unique ID for each medication record
    pet_id INT,                                     -- Which pet is taking the medication
    vet_id INT,                                     -- Which vet prescribed the medication
    medicine_name VARCHAR(100),                     -- Name of medicine (e.g., "Antibiotics", "Pain Relief")
    dosage VARCHAR(50),                             -- How much to give (e.g., "2 tablets daily")
    start_date DATE,                                -- When to start giving the medication
    end_date DATE,                                  -- When to stop giving the medication (optional)
    notes TEXT,                                     -- Additional instructions or notes
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id),           -- Ensures pet exists
    FOREIGN KEY (vet_id) REFERENCES veterinarians(vet_id)   -- Ensures vet exists
);
-- =====================================================
-- EXPENSES TABLE - Track pet care costs
-- =====================================================
-- This table helps pet owners track how much they spend on pet care
-- Useful for budgeting and expense reporting
CREATE TABLE expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,      -- Unique ID for each expense record
    owner_id INT,                                   -- Which owner paid the expense
    pet_id INT,                                     -- Which pet the expense was for
    description VARCHAR(100),                       -- What the expense was for (e.g., "Vet Visit", "Food")
    amount DECIMAL(10,2),                           -- Cost amount (up to 99,999,999.99)
    date DATE,                                      -- When the expense occurred
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id),  -- Ensures owner exists
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id)         -- Ensures pet exists
);

-- =====================================================
-- DESCRIBE TABLES - Show structure of all tables
-- =====================================================
-- These commands show the structure of each table we just created
-- Useful for verifying that tables were created correctly

DESCRIBE users;          -- Show structure of users table
DESCRIBE owners;         -- Show structure of owners table
DESCRIBE pets;           -- Show structure of pets table
DESCRIBE appointments;   -- Show structure of appointments table
DESCRIBE expenses;       -- Show structure of expenses table
DESCRIBE medications;    -- Show structure of medications table
DESCRIBE vaccinations;   -- Show structure of vaccinations table
DESCRIBE veterinarians;  -- Show structure of veterinarians table

-- =====================================================
-- DATABASE RELATIONSHIPS SUMMARY
-- =====================================================
-- Here's how the tables connect to each other:
--
-- users (main table)
--   ├── owners (user_id) - Pet owners get extra info here
--   └── veterinarians (user_id) - Vets get extra info here
--
-- owners
--   ├── pets (owner_id) - Each owner can have multiple pets
--   ├── appointments (owner_id) - Each owner can book multiple appointments
--   └── expenses (owner_id) - Each owner can have multiple expenses
--
-- pets
--   ├── appointments (pet_id) - Each pet can have multiple appointments
--   ├── vaccinations (pet_id) - Each pet can have multiple vaccinations
--   ├── medications (pet_id) - Each pet can have multiple medications
--   └── expenses (pet_id) - Each pet can have multiple expenses
--
-- veterinarians
--   ├── vaccinations (vet_id) - Each vet can give multiple vaccinations
--   └── medications (vet_id) - Each vet can prescribe multiple medications
--
-- appointments connects: owners + pets + veterinarians
-- =====================================================