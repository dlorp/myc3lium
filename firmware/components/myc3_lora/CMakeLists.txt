idf_component_register(
    SRCS
        "lora_driver.cpp"
    INCLUDE_DIRS
        "."
    REQUIRES
        "freertos"
        "esp_system"
        "driver"
)

target_compile_definitions(${COMPONENT_LIB} PRIVATE MYC3_VARIANT_LORA=1)
