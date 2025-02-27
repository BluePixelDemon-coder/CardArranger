import subprocess

# List of Python scripts to run
scripts = ["download-cards.py", "generate-png.py", "combine-pngs.py"]

for script in scripts:
    print(f"Running {script}...")
    result = subprocess.run(["python", script], capture_output=True, text=True)
    print(result.stdout)  # Print script output
    if result.returncode != 0:
        print(f"Error in {script}: {result.stderr}")
        break  # Stop execution if a script fails

print("All scripts executed!")
