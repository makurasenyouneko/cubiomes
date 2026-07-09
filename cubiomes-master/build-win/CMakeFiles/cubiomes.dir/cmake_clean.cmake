file(REMOVE_RECURSE
  "libcubiomes.dll"
  "libcubiomes.dll.a"
  "libcubiomes.pdb"
)

# Per-language clean rules from dependency scanning.
foreach(lang C)
  include(CMakeFiles/cubiomes.dir/cmake_clean_${lang}.cmake OPTIONAL)
endforeach()
