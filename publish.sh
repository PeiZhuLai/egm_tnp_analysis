#!/usr/bin/env bash
# FORCE_REGEN_HOME=1 to update the homepage but the rest of link need to be updated
# FORCE_REGEN_SUB=1 to update the homepage but the rest of link need to be updated
# FORCE_REGEN_FIT=1 to update the homepage but the rest of link need to be updated

FORCE_REGEN_HOME=1 ./publish_subpage.sh \
  --dest resolve_ph_2023postBPix/hza_resolve_phid_2023postBPix \
  --hometitle "Resolve Custom Photon ID 2023postBPix"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2023postBPix" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023postBPix_sf/plots/Data_2023postBPix/nominalFit \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023postBPix_sf \
  --section-url "#Resolve_Custom_Photon_ID_2023postBPix"

./publish_subpage.sh \
  --dest resolve_ph_2023preBPix/hza_resolve_phid_2023preBPix \
  --hometitle "Resolve Custom Photon ID 2023preBPix"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2023preBPix" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023preBPix_sf/plots/Data_2023preBPix/nominalFit \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023preBPix_sf \
  --section-url "#Resolve_Custom_Photon_ID_2023preBPix"

./publish_subpage.sh \
  --dest resolve_ph_2022postEE/hza_resolve_phid_2022postEE \
  --hometitle "Resolve Custom Photon ID 2022postEE"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2022postEE" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022postEE_sf/plots/Data_2022postEE/nominalFit \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022postEE_sf \
  --section-url "#Resolve_Custom_Photon_ID_2022postEE"

./publish_subpage.sh \
  --dest resolve_ph_2022preEE/hza_resolve_phid_2022preEE \
  --hometitle "Resolve Custom Photon ID 2022preEE"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2022preEE" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022preEE_sf/plots/Data_2022preEE/nominalFit \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022preEE_sf \
  --section-url "#Resolve_Custom_Photon_ID_2022preEE"