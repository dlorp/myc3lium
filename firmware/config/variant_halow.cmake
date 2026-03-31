set(MYC3_VARIANT_HALOW 1)
set(VARIANT_NAME "halow")
set(VARIANT_RADIO "HT-HC01P")
set(VARIANT_DISPLAY "none")

idf_component_register(
    SRCS
        "src/core/myc3_core.cpp"
        "src/main.cpp"
    INCLUDE_DIRS
        "include"
        "src/core"
        "components/myc3_halow"
    REQUIRES
        "freertos"
        "esp_system"
        "nvs_flash"
        "driver"
)

target_compile_definitions(${COMPONENT_LIB} PRIVATE MYC3_VARIANT_HALOW=1)
