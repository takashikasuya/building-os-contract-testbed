# Creating the GitHub repository (for the human approver)

None of the steps below has been executed. Run them only after every entry in
[release/approvals.yaml](../release/approvals.yaml) is approved and `python tools/release_gate.py` prints
`VERDICT: PASS`.

1. Confirm the gate and the commit identity:

   ```bash
   python tools/release_gate.py --clean-install
   git log --format='%h %an <%ae> %s'
   ```

2. Create the repository as **private** first (owner to be decided):

   ```bash
   gh repo create <owner>/building-os-contract-testbed --private --disable-wiki \
     --description "Offline contract checks for Building OS integration experiments"
   git remote add origin https://github.com/<owner>/building-os-contract-testbed.git
   git push -u origin main
   ```

3. In the private repository, check that the "Offline CI" workflow passes. Then enable private vulnerability
   reporting and secret scanning with push protection, and protect `main` so changes go through reviewed pull requests.

4. Changing visibility to public is a separate approval (`push_and_visibility`):

   ```bash
   gh repo edit <owner>/building-os-contract-testbed --visibility public --accept-visibility-change-consequences
   ```

5. Tag the first release only after the public CI run passes: `git tag -a v0.1.0 -m "First public release"`.
