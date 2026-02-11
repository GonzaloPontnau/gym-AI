import os
import shutil

def main():
    # Ensure dirs exist
    os.makedirs('docs', exist_ok=True)
    os.makedirs('scripts', exist_ok=True)

    # Move files
    files_to_docs = ['TROUBLESHOOTING_502.md', 'security.md']
    for f in files_to_docs:
        if os.path.exists(f):
            print(f"Moving {f} to docs/")
            shutil.move(f, os.path.join('docs', f))
        else:
            print(f"{f} not found, skipping.")

    files_to_scripts = ['check_health.py', 'list_gemini_models.py']
    for f in files_to_scripts:
        if os.path.exists(f):
            print(f"Moving {f} to scripts/")
            shutil.move(f, os.path.join('scripts', f))
        else:
            print(f"{f} not found, skipping.")

    # Delete logo
    if os.path.exists('logoGymAI.png'):
        print("Deleting logoGymAI.png")
        os.remove('logoGymAI.png')
    else:
        print("logoGymAI.png not found, skipping.")

if __name__ == '__main__':
    main()
