cmake_minimum_required(VERSION 3.16)

set(MYC3_VARIANT "$ENV{MYC3_VARIANT}")

if(NOT MYC3_VARIANT)
    set(MYC3_VARIANT "halow")
    message(STATUS "MYC3_VARIANT not set, defaulting to 'halow'")
endif()

message(STATUS "Building myc3lium firmware for variant: ${MYC3_VARIANT}")

if(MYC3_VARIANT STREQUAL "halow")
    message(STATUS "Variant A: HT-HC01P HaLow radio")
    add_compile_definitions(MYC3_VARIANT_HALOW=1)
elseif(MYC3_VARIANT STREQUAL "lora")
    message(STATUS "Variant B: SX1262 LoRa radio + OLED")
    add_compile_definitions(MYC3_VARIANT_LORA=1)
else()
    message(FATAL_ERROR "Unknown MYC3_VARIANT: ${MYC3_VARIANT}. Use 'halow' or 'lora'")
endif()

set(EXTRA_COMPONENT_DIRS "${CMAKE_CURRENT_SOURCE_DIR}/components")

project(myc3lium_handheld)

if(NOT DEFINED CONFIG_MYC3_NVS_ENCRYPTION OR NOT CONFIG_MYC3_NVS_ENCRYPTION)
    message(FATAL_ERROR "CONFIG_MYC3_NVS_ENCRYPTION must be enabled for secure builds")
endif()

if(NOT DEFINED CONFIG_MYC3_SECURE_BOOT OR NOT CONFIG_MYC3_SECURE_BOOT)
    message(FATAL_ERROR "CONFIG_MYC3_SECURE_BOOT must be enabled for secure builds")
endif()

if(NOT DEFINED CONFIG_MYC3_FLASH_ENCRYPTION OR NOT CONFIG_MYC3_FLASH_ENCRYPTION)
    message(FATAL_ERROR "CONFIG_MYC3_FLASH_ENCRYPTION must be enabled for secure builds")
endif()

if(NOT DEFINED CONFIG_MYC3_APP_ANTI_ROLLBACK OR NOT CONFIG_MYC3_APP_ANTI_ROLLBACK)
    message(FATAL_ERROR "CONFIG_MYC3_APP_ANTI_ROLLBACK must be enabled for secure builds")
endif()

idf_build_executable(myc3lium_handheld.elf)
