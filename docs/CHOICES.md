# Technical choices

The current, source-based account is in [design.md](design.md). The previous narrative mixed representation details with historical speed claims that the overhaul did not rerun; it remains available in Git history at `f179ae0`.

One factual correction matters: `std::vector<bool>` can use packed storage. The project's explicit `uint64_t` buffers provide direct word access and a controlled layout; the code does not demonstrate a storage-density advantage over every standard-library implementation. No new comparison of alternative containers was measured.
