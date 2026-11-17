# Frozen data identity audit

The new audit verified both manifest SHA256s, all 22,645 example IDs/sequences, numeric labels, canonical exact/RC groups, expected split counts, and zero within-task cross-split exact/RC overlap. It preserved the existing within-split splice duplicate. H3/test was previously explored; no additional dataset test members were opened. See COHORT_IDENTITY_AUDIT.json.

The [primary GUE paper, Appendix B.2](https://arxiv.org/html/2306.15006v2#A2.SS2), describes yeast histone-mark prediction, human promoter windows around TSS, human TF ChIP peaks with length/GC-matched negatives, reconstructed donor/acceptor/nonsplice examples, and mouse TF peaks with dinucleotide-shuffled negatives. This describes dataset construction, without establishing the integer-to-biological-class map in the frozen files.

Human `tf/0` and mouse `mouse/0` remain the authoritative evaluation identities. Matching their source sizes to named entries in the paper remains an inference, without an explicit alias manifest. Numeric class1 stays the binary positive convention; splice retains sorted numeric classes0/1/2 with macro-OVR metrics. No relabeling was performed.

Source-locus/genome/homology identifiers remain unavailable. Exact/RC exclusion does not establish biological independence. The [pinned official repository](https://github.com/MAGICS-LAB/DNABERT_2/tree/f25bed9ee20db966dff39e5c1571249d04e36404) supplies the benchmark origin; no training commands from its documentation were executed.

The first new checker used the wrong canonicalization order (minimum of hashes). It failed before producing a receipt. The corrected checker independently verified the historical definition: hash the lexicographically smaller of the sequence and reverse complement. Failure log retained; historical data and groups were unchanged.
