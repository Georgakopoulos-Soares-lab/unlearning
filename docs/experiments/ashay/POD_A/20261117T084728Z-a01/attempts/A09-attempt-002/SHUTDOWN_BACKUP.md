# Pod A shutdown backup index

The A09 report and public outputs are committed to research POD_A; A09 payload, final metadata and separate receipt are private and freshly verified. [Final closeout](A09_RECEIPT.json), [report](REPORT.pdf), [restore guide](RESTORE.md).

A full run-control supplement is privately stored at `ashay-sriv/undo-evo2-pilot-backup-20261020`, revision `f1860aecdc1dab2beba91ce181cb77df48d4d6c2`, path `POD_A/20261117T084728Z-a01/A09/A09-attempt-002/shutdown-001/run-control-full-001.tar.gz`, SHA256 `a01fc40a5c4855cdba4c5a71e5ca1a573ea574522a85a214a509d5d8d1986976`. Its internal manifest SHA256 is `e235dbdf1200711e8478a63cf37004e1a5a94db053f8958a293dc6fd63cb93ca`. Fresh readback verified 2912 regular members. This includes the original A09 regeneration caches and the post-exit process proof; two old Hugging Face cache symlinks are listed as exclusions in the manifest. See [machine-readable pointer](SHUTDOWN_BACKUP.json).

Use the private dataset revision and path to download into a new cache, verify size/SHA256 and every manifest entry, then follow [RESTORE.md](RESTORE.md) and the final A09 receipt for scientific dependencies. The Pod was left running; shutdown is a separate user operation.
