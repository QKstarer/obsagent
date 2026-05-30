#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     Batch 5mC Methylation Analyzer for CRISPesso            ║
║     CpG & non-CpG Methylation Ratio Calculator              ║
║     For ~86 bisulfite-seq samples                           ║
╚══════════════════════════════════════════════════════════════╝

Bisulfite conversion principle:
  - Unmethylated C → U (PCR amplified as T)
  - Methylated C (5mC) → C (protected, reads as C)
  
Sample naming convention (86 samples: S419 ~ S504):
  D:/research/.../CRISPResso/SNRPN/S{289..504}/CRISPResso_on_.../
  
  Wait - based on your for loop: for (( i=419; i <=504; i++))
  So samples are S419 through S504 = 86 samples

CRISPesso command used:
  CRISPResso -r1 Rawdata/FT150036232_L01_S$i_1.fq.gz 
             -r2 Rawdata/FT150036232_L01_S$i_2.fq.gz 
             -a <amplicon_seq> 
             -q 30 
             --min_paired_end_reads_overlap 0 
             -w 25 
             --min_frequency_alleles_around_cut_to_plot 0.01 
             --window_around_sgrna 25 
             --plot_window_size 25 
             -o CRISPResso/SNRPN/S$i

Key sequences:
  Original (unmethylated): 
    Cgctcaaatttccgcagtaggaatgctcaagcattccttttggtagctgccttttggc...
  Bisulfite-treated (methylated C→C):
    CGtttaaattttCGtagtaggaatgtttaagtattttttttggtagttgttttttgg...
  5p primer: CGtttaaattttCGtagtagg  (first 2 CG EXCLUDED)
  3p primer: actaacaaaatccaca
"""

import os
import sys
import re
import csv
import glob
import argparse
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional, Set


# ============================================================================
# Reference Sequences (from your description)
# ============================================================================

ORIGINAL_SEQ = (
    "Cgctcaaatttccgcagtaggaatgctcaagcattccttttggtagctgccttttggcaggacattccggtcagagggacagagacccctgcattgcggcaaaaatgtgcgcatgtgcagccattgcctgggacgcatgcgtagggagccgcgcgacaaacctgagccattgcggcaagactagcgcagagaggagagggagccggagatgccagacgcttggttctgaggagtgatttgcaacgcaatggagcgaggaaggtcagctgggcttgtggattctgctagc"
).upper()

# This is the amplicon sequence used in -a parameter
AMPLICON_SEQ = (
    "CGtttaaattttCGtagtaggaatgtttaagtattttttttggtagttgttttttggtaggatatttCGgttagagggatagagatttttgtattgCGgtaaaaatgtgCGtatgtgtagttattgtttgggaCGtatgCGtagggagtCGCGCGataaatttgagttattgCGgtaagattagCGtagagaggagagggagtCGgagatgttagaCGtttggttttgaggagtgatttgtaaCGtaatggagCGaggaaggttagttgggtttgtggattttgttagt"
).upper()

# Primer sequences
PRIMER_5P = "CGtttaaattttCGtagtagg".upper()  # First 2 CGs excluded
PRIMER_3P = "actaacaaaatccaca".upper()


# ============================================================================
# Functions
# ============================================================================

def find_cpg_positions_in_original(seq: str, exclude_primers: bool = True) -> Tuple[Set[int], int]:
    """
    Find all CpG positions (C in CG context) in the ORIGINAL reference sequence.
    
    Returns:
        set of 0-based positions where C is part of CpG
        number of positions excluded (primer region)
    """
    cpg_positions = set()
    for i in range(len(seq) - 1):
        if seq[i] == 'C' and seq[i+1] == 'G':
            cpg_positions.add(i)
    
    # Also handle reverse complement CpG detection
    # ... the amplicon has many CG motifs
    
    return cpg_positions


def parse_nucleotide_percentage_table(filepath: str) -> Optional[Dict]:
    """
    Parse CRISPesso's Nucleotide_percentage_table.txt.
    
    Format observed from uploaded file:
      Line 0: Reference sequence (tab-separated bases)
      Line 1: Base letter (e.g., 'C' or 't')
      Line 2: Values for next base
      Actually from the file content I read, it seems:
        - Tab-separated rows
        - First row: reference bases (single characters separated by tabs)
        - Subsequent rows: probably A, T, C, G percentages
    """
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
    except Exception as e:
        print(f"[ERROR] Cannot read {filepath}: {e}")
        return None
    
    if len(lines) < 2:
        print(f"[WARN] {filepath}: too few lines ({len(lines)})")
        return None
    
    # First line: reference sequence (tab-separated individual bases)
    ref_parts = lines[0].split('\t')
    ref_seq = ''.join(ref_parts)
    
    # Check format - parse the remaining lines
    # The CRISPesso format seems to have reference on line 1, then
    # probability values per base
    
    # Let's try to detect the format
    base_probs = {}
    
    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        
        # First element should be a base identifier
        first = parts[0].strip()
        if first in ('A', 'C', 'G', 'T', 'U', 'N', '-'):
            values = []
            for v in parts[1:]:
                try:
                    values.append(float(v))
                except ValueError:
                    values.append(0.0)
            base_probs[first] = values
    
    # If we didn't find the right format, try alternative format
    if not base_probs or len(base_probs) < 2:
        # Maybe the format is: first row is reference, next rows are counts?
        # The uploaded file shows values like: 0.9968, 0.0017, 0.0015...
        # So they are probabilities/fractions
        
        # Try to detect what format the probabilities are in
        for line in lines[1:]:
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            # Try first char as base type
            first = parts[0][0].upper() if parts[0] else ''
            if first in ('A', 'C', 'G', 'T'):
                values = []
                for v in parts[1:]:
                    try:
                        values.append(float(v))
                    except ValueError:
                        values.append(0.0)
                base_probs[first] = values
    
    return {
        'ref_seq': ref_seq,
        'ref_length': len(ref_seq),
        'base_probs': base_probs,
    }


def analyze_methylation_from_nuc_table(
    parsed: Dict,
    cpg_positions: Set[int],
    primer_5p_len: int = len(PRIMER_5P)
) -> Dict:
    """
    Analyze CpG and non-CpG methylation from parsed nucleotide table.
    
    For bisulfite sequencing:
      - At each C position in reference:
        P(C) = methylation probability (C was protected = 5mC)
        P(T) = unmethylated probability (C converted to T)
      
    Methylation ratio = P(C) / (P(C) + P(T))
    """
    ref_seq = parsed['ref_seq']
    base_probs = parsed['base_probs']
    seq_len = len(ref_seq)
    
    # Stats accumulators
    cpg_positions_data = {}       # {pos: {meth_ratio, prob_C, prob_T, ...}}
    non_cpg_positions_data = {}   # same
    
    cpg_methylated_count = 0
    cpg_unmethylated_count = 0
    non_cpg_methylated_count = 0
    non_cpg_unmethylated_count = 0
    
    cpg_methylation_ratios = []    # For quantitative average
    non_cpg_methylation_ratios = []
    
    # Get probability arrays for C and T
    prob_C = base_probs.get('C', [])
    prob_T = base_probs.get('T', [])
    
    if not prob_C and not prob_T:
        # Perhaps using "t" instead of "T" or "c" instead of "C"
        prob_C = base_probs.get('c', base_probs.get('C', []))
        prob_T = base_probs.get('t', base_probs.get('T', []))
    
    # Also check if lowercase keys exist
    for k in list(base_probs.keys()):
        if k.upper() == 'C' and k != 'C':
            prob_C = base_probs[k]
        if k.upper() == 'T' and k != 'T':
            prob_T = base_probs[k]
    
    # Make sure we have the data
    if not prob_C:
        print(f"  [WARN] No C probability data found. Available bases: {list(base_probs.keys())}")
        prob_C = [0.0] * seq_len
    if not prob_T:
        prob_T = [0.0] * seq_len
    
    # Pad arrays if needed
    while len(prob_C) < seq_len:
        prob_C.append(0.0)
    while len(prob_T) < seq_len:
        prob_T.append(0.0)
    
    # Analyze each position
    for pos in range(seq_len):
        if pos >= len(ref_seq):
            break
        
        ref_base = ref_seq[pos]
        if ref_base != 'C':
            continue
        
        # Skip positions in the 5' primer region (first 2 CGs excluded)
        if pos < primer_5p_len:
            continue
        
        pC = prob_C[pos] if pos < len(prob_C) else 0.0
        pT = prob_T[pos] if pos < len(prob_T) else 0.0
        
        total = pC + pT
        if total < 0.0001:  # Skip very low coverage
            continue
        
        meth_ratio = pC / total
        
        # Determine if CpG context
        is_cpg = pos in cpg_positions
        
        entry = {
            'pos': pos,
            'prob_C': pC,
            'prob_T': pT,
            'methylation_ratio': meth_ratio,
            'dinucleotide': ref_seq[max(0, pos-1):pos+2] if pos > 0 else ref_seq[pos:pos+2],
            'is_methylated_binary': meth_ratio > 0.5,
        }
        
        if is_cpg:
            cpg_positions_data[pos] = entry
            cpg_methylation_ratios.append(meth_ratio)
            if meth_ratio > 0.5:
                cpg_methylated_count += 1
            else:
                cpg_unmethylated_count += 1
        else:
            non_cpg_positions_data[pos] = entry
            non_cpg_methylation_ratios.append(meth_ratio)
            if meth_ratio > 0.5:
                non_cpg_methylated_count += 1
            else:
                non_cpg_unmethylated_count += 1
    
    # Calculate summary statistics
    total_cpg = cpg_methylated_count + cpg_unmethylated_count
    total_non_cpg = non_cpg_methylated_count + non_cpg_unmethylated_count
    total_all = total_cpg + total_non_cpg
    
    cpg_meth_binary = cpg_methylated_count / total_cpg if total_cpg > 0 else 0.0
    non_cpg_meth_binary = non_cpg_methylated_count / total_non_cpg if total_non_cpg > 0 else 0.0
    overall_meth_binary = (cpg_methylated_count + non_cpg_methylated_count) / total_all if total_all > 0 else 0.0
    
    cpg_meth_avg = sum(cpg_methylation_ratios) / len(cpg_methylation_ratios) if cpg_methylation_ratios else 0.0
    non_cpg_meth_avg = sum(non_cpg_methylation_ratios) / len(non_cpg_methylation_ratios) if non_cpg_methylation_ratios else 0.0
    
    total_meth_ratios = cpg_methylation_ratios + non_cpg_methylation_ratios
    overall_meth_avg = sum(total_meth_ratios) / len(total_meth_ratios) if total_meth_ratios else 0.0
    
    return {
        'ref_seq': ref_seq,
        'seq_length': seq_len,
        'total_c_positions_analyzed': total_all,
        'cpg_positions_total': total_cpg,
        'non_cpg_positions_total': total_non_cpg,
        'cpg_methylated_count': cpg_methylated_count,
        'cpg_unmethylated_count': cpg_unmethylated_count,
        'non_cpg_methylated_count': non_cpg_methylated_count,
        'non_cpg_unmethylated_count': non_cpg_unmethylated_count,
        'cpg_methylation_ratio_binary': cpg_meth_binary * 100,
        'non_cpg_methylation_ratio_binary': non_cpg_meth_binary * 100,
        'overall_methylation_ratio_binary': overall_meth_binary * 100,
        'cpg_methylation_ratio_quant': cpg_meth_avg * 100,
        'non_cpg_methylation_ratio_quant': non_cpg_meth_avg * 100,
        'overall_methylation_ratio_quant': overall_meth_avg * 100,
        'cpg_positions_data': cpg_positions_data,
        'non_cpg_positions_data': non_cpg_positions_data,
        'reference_found_in_file': len(ref_seq) > 0,
    }


def analyze_single_sample(sample_folder: str) -> Optional[Dict]:
    """
    Analyze one CRISPesso sample folder.
    
    Looks for Nucleotide_percentage_table.txt in the folder.
    """
    nuc_table_path = os.path.join(sample_folder, "Nucleotide_percentage_table.txt")
    if not os.path.exists(nuc_table_path):
        return None
    
    sample_name = os.path.basename(sample_folder)
    
    # Parse the nucleotide table
    parsed = parse_nucleotide_percentage_table(nuc_table_path)
    if parsed is None:
        return None
    
    ref_seq = parsed['ref_seq']
    
    # Determine: is the reference sequence from CRISPesso the original amplicon
    # or the bisulfite-treated version?
    # 
    # The CRISPesso command uses the AMPLICON_SEQ (bisulfite-treated) as -a parameter.
    # So CRISPesso's reference should be the bisulfite-treated amplicon.
    #
    # For CpG position detection, we need to find all CG dinucleotides
    # Since the reference IS already bisulfite-treated:
    #   - Every C in the reference represents a methylated C (protected)
    #   - Every T that was originally C represents unmethylated C
    #
    # CpG positions: look at where there's a 'C' followed by 'G' in the reference
    # (the reference is bisulfite-treated, so only methylated C's show as C)
    # BUT we need to find ALL potential CpG positions from the ORIGINAL sequence
    
    # Find all CG dinucleotide positions in the AMPLICON (which represents
    # the fully methylated version). These are the positions where CpG 
    # methylation could occur.
    amplicon_cpg_positions = find_cpg_positions_in_original(AMPLICON_SEQ)
    
    # Also check: do we have all CpG positions from original seq?
    # Let's also check ORIGINAL_SEQ to be thorough
    original_cpg = set()
    for i in range(len(ORIGINAL_SEQ) - 1):
        if ORIGINAL_SEQ[i] == 'C' and ORIGINAL_SEQ[i+1] == 'G':
            original_cpg.add(i)
    
    # The amplicon sequence starts at some offset from the original
    # Let's compare to figure out the exact overlap
    # Actually, looking at the sequences:
    ORIGINAL_START_IN_AMPLICON = 0  # They start at same position
    
    # Map CpG positions from original to amplicon coordinates
    # But the amplicon is already bisulfite-converted, so we use amplicon directly
    # Find all 'CG' in the amplicon sequence
    cpg_positions_from_amplicon = set()
    for i in range(len(AMPLICON_SEQ) - 1):
        if AMPLICON_SEQ[i] == 'C' and AMPLICON_SEQ[i+1] == 'G':
            cpg_positions_from_amplicon.add(i)
    
    # Now we also need to be careful: the CRISPesso reference might be shorter
    # than the full amplicon (CRISPesso trims based on read alignment)
    # Let's find the overlap between CRISPesso ref and amplicon
    
    # Actually, a simpler approach: 
    # In the bisulfite-treated reference used by CRISPesso:
    #   - 'C' at a position = methylation detected
    #   - 'T' at a position = no methylation (if the original was C)
    # 
    # For CpG methylation: check positions where original seq has CG
    # For non-CpG methylation: check positions where original seq has C but not CG
    
    # Since CRISPesso uses the bisulfite-treated amplicon as reference,
    # we need to align the CRISPesso ref back to the original sequence
    
    # SIMPLEST APPROACH: 
    # Use the CRISPesso reference sequence directly.
    # The reference from CRISPesso file is the sequence provided via -a,
    # which is the BISULFITE-TREATED sequence.
    # 
    # In this reference: 
    #   - C means a methylated CG (CpG) that was protected
    #   - T means either an unmethylated C or a native T
    #
    # So we find CG dinucleotides in the AMPLICON (bisulfite ref),
    # and check methylation at those positions
    
    # But we also need to know which positions in the CRISPesso ref 
    # correspond to the amplicon positions
    
    # Let's just use the ref_seq from the CRISPesso output directly
    # and find CG dinucleotides in it
    
    ref_cpg_positions = set()
    for i in range(len(ref_seq) - 1):
        if ref_seq[i] == 'C' and ref_seq[i+1] == 'G':
            ref_cpg_positions.add(i)
    
    # Also find C positions that are NOT in CG context (non-CpG)
    # In the bisulfite-treated reference, if we see a C not in CG context,
    # it might be non-CpG methylation (rare but possible)
    
    # But wait - the original sequence has Cs in both CpG and non-CpG contexts.
    # The bisulfite treatment converts unmethylated C to T regardless of context.
    # So in the bisulfite-treated reference:
    #   - If we see 'C', it was methylated (could be CpG or non-CpG)
    #   - If we see 'T', it's ambiguous (could be native T or unmethylated C)
    
    # So for the CRISPesso analysis:
    # The reference (amplicon) already has C only at methylated positions.
    # The probability tables show how many reads support each base.
    # At positions where ref is C: P(C) = methylation support
    # At positions where ref is T (but originally was C): P(T) = no methylation
    # But we can't distinguish native T from converted T in the reference...
    
    # ACTUAL CORRECT APPROACH:
    # Use the ORIGINAL_SEQ to find all C positions (both CpG and non-CpG).
    # For each C position in original seq, check the bisulfite data:
    #   - High P(C) = methylated
    #   - High P(T) = unmethylated
    # This works regardless of what the CRISPesso reference sequence shows.
    
    # Find all C positions in original sequence
    original_c_positions = set()
    for i in range(len(ORIGINAL_SEQ)):
        if ORIGINAL_SEQ[i] == 'C':
            original_c_positions.add(i)
    
    # Find which ones are CpG
    original_cpg = set()
    for i in range(len(ORIGINAL_SEQ) - 1):
        if ORIGINAL_SEQ[i] == 'C' and ORIGINAL_SEQ[i+1] == 'G':
            original_cpg.add(i)
    
    # Now, we need to map original positions to the CRISPesso reference positions.
    # The amplicon (used as -a) covers the same region as the original but 
    # with bisulfite conversion (C→T except methylated C→C).
    
    # Let's do a proper alignment between original and amplicon
    # to figure out the position mapping
    
    alignment = align_sequences(ORIGINAL_SEQ, AMPLICON_SEQ)
    
    if alignment:
        # Use the alignment to map positions
        orig_to_amplicon = alignment['orig_to_amplicon']  # Dict mapping orig pos -> amplicon pos
        
        # Map original CpG positions to amplicon coordinates
        cpg_positions_in_amplicon = set()
        for orig_pos in original_cpg:
            if orig_pos in orig_to_amplicon:
                cpg_positions_in_amplicon.add(orig_to_amplicon[orig_pos])
            else:
                # If not in amplicon, maybe it's outside the amplified region
                pass
        
        # Map all original C positions to amplicon coordinates
        all_c_in_amplicon = set()
        for orig_pos in original_c_positions:
            if orig_pos in orig_to_amplicon:
                all_c_in_amplicon.add(orig_to_amplicon[orig_pos])
        
        # Also handle the reverse: non-CpG C positions = all C minus CpG
        non_cpg_positions_in_amplicon = all_c_in_amplicon - cpg_positions_in_amplicon
        
    else:
        # Fallback: use direct position mapping (same coordinates)
        cpg_positions_in_amplicon = original_cpg
        non_cpg_positions_in_amplicon = original_c_positions - original_cpg
    
    # Now, CRISPesso's reference might be a subset of the amplicon
    # (due to read alignment trimming). We need to find the overlap.
    # The ref_seq from the file is what CRISPesso used as reference.
    
    # Align ref_seq to amplicon to find offset
    ref_start_in_amplicon = 0
    
    # Simple approach: find where ref_seq starts in amplicon
    if len(ref_seq) > 20:
        # Use first 20 bases as anchor
        anchor = ref_seq[:20]
        idx = AMPLICON_SEQ.find(anchor)
        if idx >= 0:
            ref_start_in_amplicon = idx
    
    # Now filter to only positions within the CRISPesso reference window
    ref_end = ref_start_in_amplicon + len(ref_seq)
    
    cpg_in_ref_window = {p for p in cpg_positions_in_amplicon 
                         if ref_start_in_amplicon <= p < ref_end}
    non_cpg_in_ref_window = {p for p in non_cpg_positions_in_amplicon 
                             if ref_start_in_amplicon <= p < ref_end}
    
    # Convert to local (0-based within ref_seq) coordinates
    cpg_local = {p - ref_start_in_amplicon for p in cpg_in_ref_window}
    non_cpg_local = {p - ref_start_in_amplicon for p in non_cpg_in_ref_window}
    
    # Now analyze methylation using the probability data
    result = analyze_methylation_from_nuc_table(parsed, cpg_local)
    
    # But we need to override: the cpg_positions passed above might not
    # be correct if our alignment approach is flawed.
    # Let's directly compute using the local position mapping.
    
    # Re-do the analysis with proper CpG positions
    prob_C = parsed['base_probs'].get('C', [])
    prob_T = parsed['base_probs'].get('T', [])
    
    # Fill to seq length
    while len(prob_C) < len(ref_seq):
        prob_C.append(0.0)
    while len(prob_T) < len(ref_seq):
        prob_T.append(0.0)
    
    # Also get G and A probabilities for checking
    prob_G = parsed['base_probs'].get('G', [])
    prob_A = parsed['base_probs'].get('A', [])
    while len(prob_G) < len(ref_seq):
        prob_G.append(0.0)
    while len(prob_A) < len(ref_seq):
        prob_A.append(0.0)
    
    cpg_data = {}
    non_cpg_data = {}
    
    cpg_meth_count = 0
    cpg_unmeth_count = 0
    non_cpg_meth_count = 0
    non_cpg_unmeth_count = 0
    
    cpg_ratios = []
    non_cpg_ratios = []
    
    # For reference: the ref_seq from CRISPesso is the bisulfite-converted amplicon.
    # In this reference:
    #   - C at position means the original C was methylated (in the reference sequence itself)
    #   - But the reference is just a template - the actual data is in the probability table
    #
    # For EACH position in ref_seq that corresponds to a C in the ORIGINAL sequence:
    #   P(C) = fraction of reads showing C = methylation
    #   P(T) = fraction of reads showing T = no methylation
    
    for local_pos in range(len(ref_seq)):
        # Check if this ref position maps to a C in original
        amplicon_pos = local_pos + ref_start_in_amplicon
        
        if amplicon_pos >= len(ORIGINAL_SEQ):
            continue
        
        orig_base = ORIGINAL_SEQ[amplicon_pos]
        if orig_base != 'C':
            continue
        
        # Skip primer region
        if amplicon_pos < len(PRIMER_5P):
            continue
        
        is_cpg = amplicon_pos in original_cpg
        
        pC = prob_C[local_pos] if local_pos < len(prob_C) else 0.0
        pT = prob_T[local_pos] if local_pos < len(prob_T) else 0.0
        
        total = pC + pT
        if total < 0.0001:
            # Try including other bases
            pG = prob_G[local_pos] if local_pos < len(prob_G) else 0.0
            pA = prob_A[local_pos] if local_pos < len(prob_A) else 0.0
            total = pC + pT + pG + pA
            if total < 0.0001:
                continue
        
        meth_ratio = pC / total if total > 0 else 0.0
        is_meth = meth_ratio > 0.5
        
        entry = {
            'amplicon_pos': amplicon_pos,
            'local_pos': local_pos,
            'orig_seq_base': orig_base,
            'ref_base': ref_seq[local_pos],
            'prob_C': pC,
            'prob_T': pT,
            'methylation_ratio': meth_ratio,
            'is_methylated': is_meth,
            'context': 'CpG' if is_cpg else 'non-CpG',
            'dinucleotide': ORIGINAL_SEQ[max(0, amplicon_pos-1):amplicon_pos+2] if amplicon_pos > 0 else ORIGINAL_SEQ[amplicon_pos:amplicon_pos+2],
        }
        
        if is_cpg:
            cpg_data[amplicon_pos] = entry
            cpg_ratios.append(meth_ratio)
            if is_meth:
                cpg_meth_count += 1
            else:
                cpg_unmeth_count += 1
        else:
            non_cpg_data[amplicon_pos] = entry
            non_cpg_ratios.append(meth_ratio)
            if is_meth:
                non_cpg_meth_count += 1
            else:
                non_cpg_unmeth_count += 1
    
    total_cpg = cpg_meth_count + cpg_unmeth_count
    total_non_cpg = non_cpg_meth_count + non_cpg_unmeth_count
    total_all = total_cpg + total_non_cpg
    
    result = {
        'sample_name': sample_name,
        'sample_folder': sample_folder,
        'cpg_positions_total': total_cpg,
        'non_cpg_positions_total': total_non_cpg,
        'total_c_positions': total_all,
        'cpg_methylated': cpg_meth_count,
        'cpg_unmethylated': cpg_unmeth_count,
        'non_cpg_methylated': non_cpg_meth_count,
        'non_cpg_unmethylated': non_cpg_unmeth_count,
        'cpg_methylation_binary_pct': round(cpg_meth_count / total_cpg * 100, 2) if total_cpg > 0 else 0.0,
        'non_cpg_methylation_binary_pct': round(non_cpg_meth_count / total_non_cpg * 100, 2) if total_non_cpg > 0 else 0.0,
        'overall_methylation_binary_pct': round((cpg_meth_count + non_cpg_meth_count) / total_all * 100, 2) if total_all > 0 else 0.0,
        'cpg_methylation_quant_pct': round(sum(cpg_ratios) / len(cpg_ratios) * 100, 2) if cpg_ratios else 0.0,
        'non_cpg_methylation_quant_pct': round(sum(non_cpg_ratios) / len(non_cpg_ratios) * 100, 2) if non_cpg_ratios else 0.0,
        'overall_methylation_quant_pct': round((sum(cpg_ratios) + sum(non_cpg_ratios)) / (len(cpg_ratios) + len(non_cpg_ratios)) * 100, 2) if (cpg_ratios or non_cpg_ratios) else 0.0,
        'cpg_data': cpg_data,
        'non_cpg_data': non_cpg_data,
        'ref_len': len(ref_seq),
        'ref_start_in_amplicon': ref_start_in_amplicon,
    }
    
    return result


def align_sequences(seq1: str, seq2: str) -> Optional[Dict]:
    """
    Simple alignment to find mapping between sequences.
    This handles the case where seq2 is a bisulfite-converted version of seq1.
    
    Returns dict with mapping info.
    """
    # Simple approach: try to find seq2 start in seq1
    # But seq2 is bisulfite-converted (C→T except methylated C→C)
    # So direct string matching won't work perfectly
    
    # Use a fuzzy match: for each position in seq2, find best matching position in seq1
    
    # Actually, since both sequences are the same length and represent
    # the same region, we can use direct position mapping.
    if len(seq1) == len(seq2):
        return {
            'orig_to_amplicon': {i: i for i in range(len(seq1))},
            'offset': 0,
        }
    
    # Try to find the offset by matching a small window
    # Look for a distinctive pattern
    for offset in range(0, max(len(seq1), len(seq2))):
        match_count = 0
        total = min(len(seq1) - offset, len(seq2))
        if total < 20:
            break
        for i in range(total):
            if seq1[offset + i] == seq2[i]:
                match_count += 1
        match_rate = match_count / total
        if match_rate > 0.7:  # 70% match (accounting for bisulfite changes)
            mapping = {}
            for i in range(total):
                mapping[offset + i] = i
            return {
                'orig_to_amplicon': mapping,
                'offset': offset,
            }
    
    return None


def discover_samples(base_dir: str, sample_ids: Optional[List[str]] = None) -> List[str]:
    """
    Discover CRISPesso sample folders.
    
    Expected structure:
      base_dir/CRISPResso/SNRPN/S{id}/CRISPResso_on_*/Nucleotide_percentage_table.txt
    
    Or from your example:
      .../SNRPN/S289/CRISPResso_on_FT150036232_L01_S289_1_FT150036232_L01_S289_2/
    """
    sample_folders = []
    
    # If specific sample IDs given, look for those
    if sample_ids:
        for sid in sample_ids:
            # Search pattern: find folders containing Nucleotide_percentage_table.txt
            # with S{sid} in the path
            pattern = os.path.join(base_dir, f"**/*S{sid}*")
            matches = glob.glob(pattern, recursive=True)
            
            for m in matches:
                if os.path.isdir(m):
                    # Check if this folder or any subfolder has the nuc table
                    nuc_table = os.path.join(m, "Nucleotide_percentage_table.txt")
                    if os.path.exists(nuc_table):
                        sample_folders.append(m)
                        break
                    # Check one level down
                    for root, dirs, files in os.walk(m):
                        if "Nucleotide_percentage_table.txt" in files:
                            sample_folders.append(root)
                            break
                        if "nucleotide_percentage_table.txt" in files:
                            sample_folders.append(root)
                            break
    
    # If no specific IDs, discover all
    if not sample_folders:
        for root, dirs, files in os.walk(base_dir):
            if "Nucleotide_percentage_table.txt" in files:
                sample_folders.append(root)
    
    # Deduplicate and sort
    sample_folders = sorted(set(sample_folders))
    
    return sample_folders


def get_sample_id_from_folder(folder_path: str) -> str:
    """Extract sample ID from folder path."""
    # Try to find S### pattern
    match = re.search(r'S(\d+)', folder_path)
    if match:
        return f"S{match.group(1)}"
    return os.path.basename(folder_path)


# ============================================================================
# Output Functions
# ============================================================================

def write_summary_csv(results: List[Dict], output_path: str):
    """Write summary CSV for all samples."""
    fieldnames = [
        'sample_id',
        'sample_folder',
        'cpg_positions_total',
        'non_cpg_positions_total',
        'total_c_positions',
        'cpg_methylated',
        'cpg_unmethylated',
        'non_cpg_methylated',
        'non_cpg_unmethylated',
        'cpg_methylation_binary_pct',
        'non_cpg_methylation_binary_pct',
        'overall_methylation_binary_pct',
        'cpg_methylation_quant_pct',
        'non_cpg_methylation_quant_pct',
        'overall_methylation_quant_pct',
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, '') for k in fieldnames}
            row['sample_folder'] = os.path.basename(row.get('sample_folder', ''))
            writer.writerow(row)
    
    print(f"[SAVED] Summary CSV: {output_path}")


def write_detailed_report(result: Dict, output_path: str):
    """Write detailed per-sample methylation report."""
    with open(output_path, 'w') as f:
        f.write(f"{'='*65}\n")
        f.write(f"  5mC Methylation Analysis Report\n")
        f.write(f"  Sample: {result['sample_name']}\n")
        f.write(f"{'='*65}\n\n")
        
        f.write(f"Reference length: {result['ref_len']} bases\n")
        f.write(f"Ref start in amplicon: position {result['ref_start_in_amplicon']}\n\n")
        
        f.write(f"{'─'*65}\n")
        f.write(f"  OVERALL SUMMARY\n")
        f.write(f"{'─'*65}\n\n")
        f.write(f"{'Metric':<35} {'Count':<15} {'Binary %':<15} {'Quant %':<15}\n")
        f.write(f"{'─'*80}\n")
        f.write(f"{'CpG positions':<35} {result['cpg_positions_total']:<15} "
                f"{result['cpg_methylation_binary_pct']:<15.2f} {result['cpg_methylation_quant_pct']:<15.2f}\n")
        f.write(f"{'Non-CpG positions':<35} {result['non_cpg_positions_total']:<15} "
                f"{result['non_cpg_methylation_binary_pct']:<15.2f} {result['non_cpg_methylation_quant_pct']:<15.2f}\n")
        f.write(f"{'Total C positions':<35} {result['total_c_positions']:<15} "
                f"{result['overall_methylation_binary_pct']:<15.2f} {result['overall_methylation_quant_pct']:<15.2f}\n")
        f.write(f"\n")
        f.write(f"{'CpG methylated':<35} {result['cpg_methylated']:<15}\n")
        f.write(f"{'CpG unmethylated':<35} {result['cpg_unmethylated']:<15}\n")
        f.write(f"{'Non-CpG methylated':<35} {result['non_cpg_methylated']:<15}\n")
        f.write(f"{'Non-CpG unmethylated':<35} {result['non_cpg_unmethylated']:<15}\n\n")
        
        # CpG details
        f.write(f"{'─'*65}\n")
        f.write(f"  CpG POSITION DETAILS (Sorted by methylation ratio)\n")
        f.write(f"{'─'*65}\n\n")
        if result['cpg_data']:
            f.write(f"{'AmpliconPos':<15} {'LocalPos':<10} {'OrigCtx':<12} {'P(C)':<12} {'P(T)':<12} {'Meth%':<10} {'Status':<10}\n")
            f.write(f"{'─'*81}\n")
            for pos in sorted(result['cpg_data'].keys()):
                d = result['cpg_data'][pos]
                status = "★METH" if d['is_methylated'] else "unmeth"
                f.write(f"{d['amplicon_pos']:<15} {d['local_pos']:<10} {d['dinucleotide']:<12} "
                        f"{d['prob_C']:<12.4f} {d['prob_T']:<12.4f} "
                        f"{d['methylation_ratio']*100:<8.2f}% {status:<10}\n")
        else:
            f.write("  (No CpG positions found)\n")
        
        f.write("\n")
        
        # Non-CpG details
        f.write(f"{'─'*65}\n")
        f.write(f"  Non-CpG POSITION DETAILS\n")
        f.write(f"{'─'*65}\n\n")
        if result['non_cpg_data']:
            f.write(f"{'AmpliconPos':<15} {'LocalPos':<10} {'OrigCtx':<12} {'P(C)':<12} {'P(T)':<12} {'Meth%':<10} {'Status':<10}\n")
            f.write(f"{'─'*81}\n")
            for pos in sorted(result['non_cpg_data'].keys()):
                d = result['non_cpg_data'][pos]
                status = "METH" if d['is_methylated'] else "unmeth"
                f.write(f"{d['amplicon_pos']:<15} {d['local_pos']:<10} {d['dinucleotide']:<12} "
                        f"{d['prob_C']:<12.4f} {d['prob_T']:<12.4f} "
                        f"{d['methylation_ratio']*100:<8.2f}% {status:<10}\n")
        else:
            f.write("  (No non-CpG positions found)\n")
        
        f.write(f"\n{'='*65}\n")
        f.write(f"  Report End\n")
        f.write(f"{'='*65}\n")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Batch 5mC Methylation Analyzer for CRISPesso Bisulfite-seq Samples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Sample range: S419 ~ S504 (86 samples)
Expected structure:
  <base_dir>/CRISPResso/SNRPN/S{{id}}/CRISPResso_on_*/Nucleotide_percentage_table.txt

Example:
  python methylation_analyzer.py -i D:/research/SNRPN/ -o ./results/
  python methylation_analyzer.py -i D:/research/SNRPN/ --samples 419-504 -o ./results/
  python methylation_analyzer.py -i D:/research/SNRPN/ --single S289 -o ./results/
        """
    )
    
    parser.add_argument('-i', '--input', required=True, help='Base directory containing CRISPesso output folders')
    parser.add_argument('-o', '--output', default='./methylation_results', help='Output directory')
    parser.add_argument('--samples', type=str, help='Sample range (e.g., 419-504 or comma-separated 419,420,421)')
    parser.add_argument('--single', type=str, help='Analyze a single sample (e.g., S289)')
    parser.add_argument('--list-samples', action='store_true', help='List discovered samples and exit')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress progress output')
    
    args = parser.parse_args()
    
    base_dir = args.input
    if not os.path.isdir(base_dir):
        print(f"[ERROR] Directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Determine sample IDs to look for
    sample_ids = []
    if args.single:
        sample_ids = [args.single]
    elif args.samples:
        if '-' in args.samples:
            parts = args.samples.split('-')
            start = int(parts[0])
            end = int(parts[1])
            sample_ids = [f"S{i}" for i in range(start, end + 1)]
        elif ',' in args.samples:
            sample_ids = [f"S{x.strip()}" for x in args.samples.split(',') if x.strip().isdigit()]
        else:
            sample_ids = [f"S{args.samples}"]
    
    # Discover sample folders
    sample_folders = discover_samples(base_dir, sample_ids if sample_ids else None)
    
    if args.list_samples:
        print(f"\nDiscovered {len(sample_folders)} sample(s):")
        for sf in sample_folders:
            sid = get_sample_id_from_folder(sf)
            print(f"  {sid:<10} → {sf}")
        sys.exit(0)
    
    if not sample_folders:
        print(f"[ERROR] No CRISPesso sample folders found in {base_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n{'='*65}")
    print(f"  Batch 5mC Methylation Analysis")
    print(f"  Found {len(sample_folders)} sample(s)")
    print(f"{'='*65}\n")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Analyze all samples
    results = []
    for sf in sample_folders:
        sid = get_sample_id_from_folder(sf)
        
        if not args.quiet:
            print(f"  [{len(results)+1}/{len(sample_folders)}] {sid}...", end=' ')
        
        result = analyze_single_sample(sf)
        
        if result:
            results.append(result)
            if not args.quiet:
                print(f"OK  CpG={result['cpg_methylation_quant_pct']:.1f}%  nonCpG={result['non_cpg_methylation_quant_pct']:.1f}%")
            
            # Write detailed report
            report_path = os.path.join(args.output, f"{sid}_methylation_report.txt")
            write_detailed_report(result, report_path)
        else:
            if not args.quiet:
                print(f"FAIL (no Nucleotide_percentage_table.txt found)")
    
    if not results:
        print("\n[ERROR] No samples could be analyzed successfully!", file=sys.stderr)
        sys.exit(1)
    
    # Write summary CSV
    summary_path = os.path.join(args.output, "methylation_summary.csv")
    write_summary_csv(results, summary_path)
    
    # Print final summary table
    print(f"\n{'='*100}")
    print(f"{'Sample':<15} {'CpG_pos':<10} {'nonCpG_pos':<12} {'CpG_meth%':<12} {'nonCpG_meth%':<14} {'Overall%':<10} {'CpG_quant%':<12}")
    print(f"{'─'*85}")
    for r in results:
        print(f"{r['sample_name']:<15} {r['cpg_positions_total']:<10} {r['non_cpg_positions_total']:<12} "
              f"{r['cpg_methylation_binary_pct']:<10.2f}%  {r['non_cpg_methylation_binary_pct']:<10.2f}%  "
              f"{r['overall_methylation_binary_pct']:<8.2f}% {r['cpg_methylation_quant_pct']:<10.2f}%")
    print(f"{'─'*85}")
    
    print(f"\n{'='*65}")
    print(f"  Analysis Complete! ({len(results)} samples)")
    print(f"  Summary:    {summary_path}")
    print(f"  Reports:    {args.output}/")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()