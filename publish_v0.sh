#!/usr/bin/env bash
# FORCE_REGEN_HOME=1 to update the homepage but the rest of link need to be updated
# FORCE_REGEN_SUB=1 to update the homepage but the rest of link need to be updated
# FORCE_REGEN_FIT=1 to update the homepage but the rest of link need to be updated

# The last line of the homepage
# publish_subpage.sh  (v2: default /eos/user/p/pelai/www/HZa/sfs)
# Show the oder reversely

# Electron Trigger SFs
# Double Trigger Lower Leg 12
./publish_subpage.sh \
  --dest resolve_dielleg12trigger_gap_2024/htoza_dielleg12trigger_gap_2024_sf \
  --hometitle "Custom Electron Double Lower Leg Trigger12 Gap 2024" \
  --title "Efficiency / Scale Factor Measurements — htoza_dielleg12trigger_gap_2024_sf" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/htoza_dielleg12trigger_gap_2024_sf/plots/Data_2024 \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/htoza_dielleg12trigger_gap_2024_sf \
  --section-url "#Resolve_Electron_Double_Lower_Trigger12_gap_2024"

./publish_subpage.sh \
  --dest resolve_dielleg12trigger_nongap_2024/htoza_dielleg12trigger_nongap_2024_sf \
  --hometitle "Custom Electron Double Lower Leg Trigger12 Nongap 2024" \
  --title "Efficiency / Scale Factor Measurements — htoza_dielleg12trigger_nongap_2024_sf" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/htoza_dielleg12trigger_nongap_2024_sf/plots/Data_2024 \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/htoza_dielleg12trigger_nongap_2024_sf \
  --section-url "#Resolve_Electron_Double_Lower_Trigger12_nongap_2024"

# Double Trigger Upper Leg 23
./publish_subpage.sh \
  --dest resolve_dielleg23trigger_gap_2024/htoza_dielleg23trigger_gap_2024_sf \
  --hometitle "Custom Electron Double Upper Leg Trigger23 Gap 2024" \
  --title "Efficiency / Scale Factor Measurements — htoza_dielleg23trigger_gap_2024_sf" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/htoza_dielleg23trigger_gap_2024_sf/plots/Data_2024 \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/htoza_dielleg23trigger_gap_2024_sf \
  --section-url "#Resolve_Electron_Double_Upper_Trigger23_gap_2024"

./publish_subpage.sh \
  --dest resolve_dielleg23trigger_nongap_2024/htoza_dielleg23trigger_nongap_2024_sf \
  --hometitle "Custom Electron Double Upper Leg Trigger23 Nongap 2024" \
  --title "Efficiency / Scale Factor Measurements — htoza_dielleg23trigger_nongap_2024_sf" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/htoza_dielleg23trigger_nongap_2024_sf/plots/Data_2024 \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/htoza_dielleg23trigger_nongap_2024_sf \
  --section-url "#Resolve_Electron_Double_Upper_Trigger23_nongap_2024"

# Single Trigger 30
./publish_subpage.sh \
  --dest resolve_sielleg30trigger_gap_2024/htoza_sielleg30trigger_gap_2024_sf \
  --hometitle "Custom Electron Single Trigger30 Gap 2024" \
  --title "Efficiency / Scale Factor Measurements — htoza_sielleg30trigger_gap_2024_sf" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/htoza_sielleg30trigger_gap_2024_sf/plots/Data_2024 \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/htoza_sielleg30trigger_gap_2024_sf \
  --section-url "#Resolve_Electron_Single_Trigger30_gap_2024"

./publish_subpage.sh \
  --dest resolve_sielleg30trigger_nongap_2024/htoza_sielleg30trigger_nongap_2024_sf \
  --hometitle "Custom Electron Single Trigger30 Nongap 2024" \
  --title "Efficiency / Scale Factor Measurements — htoza_sielleg30trigger_nongap_2024_sf" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/htoza_sielleg30trigger_nongap_2024_sf/plots/Data_2024 \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/htoza_sielleg30trigger_nongap_2024_sf \
  --section-url "#Resolve_Electron_Single_Trigger30_nongap_2024"

# Electron ID
./publish_subpage.sh \
  --dest resolve_elid_gap_2024/hza_elid_gap_2024_sf \
  --hometitle "Custom Electron ID Gap 2024" \
  --title "Efficiency / Scale Factor Measurements — hza_elid_gap_2024_sf" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_elid_nongap_2024_sf/plots/Data_2024 \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_elid_gap_2024_sf \
  --section-url "#Resolve_Electron_ID_gap_2024"

./publish_subpage.sh \
  --dest resolve_elid_nongap_2024/hza_elid_nongap_2024_sf \
  --hometitle "Custom Electron ID Nongap 2024" \
  --title "Efficiency / Scale Factor Measurements — hza_elid_nongap_2024_sf" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_elid_nongap_2024_sf/plots/Data_2024 \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_elid_nongap_2024_sf \
  --section-url "#Resolve_Electron_ID_nongap_2024"
# ----------------------------------------------------------------------------------------------
# Photon Custom ID
# Low pT
./publish_subpage.sh \
  --dest resolve_ph_lowpt_2023postBPix/hza_resolve_phid_lowpt_2024 \
  --hometitle "Resolve Custom Photon ID Low pT 2024"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_lowpt_2024" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2024_sf/plots/Data_2024C \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2024_sf \
  --section-url "#Resolve_Custom_Photon_ID_lowpt_2024"

./publish_subpage.sh \
  --dest resolve_ph_lowpt_2023postBPixHole/hza_resolve_phid_lowpt_2023postBPixHole \
  --hometitle "Resolve Custom Photon ID Low pT 2023postBPixHole"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_lowpt_2023postBPixHole" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2023postBPixHole_sf/plots/Data_2023postBPix \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2023postBPixHole_sf \
  --section-url "#Resolve_Custom_Photon_ID_lowpt_2023postBPixHole"

./publish_subpage.sh \
  --dest resolve_ph_lowpt_2023postBPix/hza_resolve_phid_lowpt_2023postBPix \
  --hometitle "Resolve Custom Photon ID Low pT 2023postBPix"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_lowpt_2023postBPix" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2023postBPix_sf/plots/Data_2023postBPix \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2023postBPix_sf \
  --section-url "#Resolve_Custom_Photon_ID_lowpt_2023postBPix"

./publish_subpage.sh \
  --dest resolve_ph_lowpt_2023preBPix/hza_resolve_phid_lowpt_2023preBPix \
  --hometitle "Resolve Custom Photon ID Low pT 2023preBPix"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_lowpt_2023preBPix" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2023preBPix_sf/plots/Data_2023preBPix \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2023preBPix_sf \
  --section-url "#Resolve_Custom_Photon_ID_lowpt_2023preBPix"

./publish_subpage.sh \
  --dest resolve_ph_lowpt_2022postEE/hza_resolve_phid_lowpt_2022postEE \
  --hometitle "Resolve Custom Photon ID Low pT 2022postEE"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_lowpt_2022postEE" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2022postEE_sf/plots/Data_2022postEE \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2022postEE_sf \
  --section-url "#Resolve_Custom_Photon_ID_lowpt_2022postEE"

./publish_subpage.sh \
  --dest resolve_ph_lowpt_2022preEE/hza_resolve_phid_lowpt_2022preEE \
  --hometitle "Resolve Custom Photon ID Low pT 2022preEE"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_lowpt_2022preEE" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2022preEE_sf/plots/Data_2022preEE \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_lowpt_2022preEE_sf \
  --section-url "#Resolve_Custom_Photon_ID_lowpt_2022preEE"

# High pT
./publish_subpage.sh \
  --dest resolve_ph_2023postBPix/hza_resolve_phid_2024 \
  --hometitle "Resolve Custom Photon ID 2024"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2024" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2024_sf/plots/Data_2024C \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2024_sf \
  --section-url "#Resolve_Custom_Photon_ID_2024"

./publish_subpage.sh \
  --dest resolve_ph_2023postBPixHole/hza_resolve_phid_2023postBPixHole \
  --hometitle "Resolve Custom Photon ID 2023postBPixHole"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2023postBPixHole" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023postBPixHole_sf/plots/Data_2023postBPix \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023postBPixHole_sf \
  --section-url "#Resolve_Custom_Photon_ID_2023postBPixHole"

./publish_subpage.sh \
  --dest resolve_ph_2023postBPix/hza_resolve_phid_2023postBPix \
  --hometitle "Resolve Custom Photon ID 2023postBPix"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2023postBPix" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023postBPix_sf/plots/Data_2023postBPix \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023postBPix_sf \
  --section-url "#Resolve_Custom_Photon_ID_2023postBPix"

./publish_subpage.sh \
  --dest resolve_ph_2023preBPix/hza_resolve_phid_2023preBPix \
  --hometitle "Resolve Custom Photon ID 2023preBPix"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2023preBPix" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023preBPix_sf/plots/Data_2023preBPix \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2023preBPix_sf \
  --section-url "#Resolve_Custom_Photon_ID_2023preBPix"

./publish_subpage.sh \
  --dest resolve_ph_2022postEE/hza_resolve_phid_2022postEE \
  --hometitle "Resolve Custom Photon ID 2022postEE"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2022postEE" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022postEE_sf/plots/Data_2022postEE \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022postEE_sf \
  --section-url "#Resolve_Custom_Photon_ID_2022postEE"

./publish_subpage.sh \
  --dest resolve_ph_2022preEE/hza_resolve_phid_2022preEE \
  --hometitle "Resolve Custom Photon ID 2022preEE"\
  --title "Efficiency / Scale Factor Measurements — hza_resolve_phid_2022preEE" \
  --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022preEE_sf/plots/Data_2022preEE \
  --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022preEE_sf \
  --section-url "#Resolve_Custom_Photon_ID_2022preEE"

# The first line of the homepage