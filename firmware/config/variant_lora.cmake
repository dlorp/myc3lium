set(MYC3_VARIANT_LORA 1)
set(VARIANT_NAME "lora")
set(VARIANT_RADIO "SX1262")
set(VARIANT_DISPLAY "SSD1306_OLED")

idf_component_register(
    SRCS
        "src/lora/lora_driver.cpp"
        "src/core/myc3_core.cpp"
        "src/main.cpp"
    INCLUDE_DIRS
        "include"
        "src/core"
        "src/lora"
    REQUIRES
        "freertos"
        "esp_system"
        "nvs_flash"
        "driver"
)

target_compile_definitions(${COMPONENT_LIB} PRIVATE MYC3_VARIANT_LORA=1)
