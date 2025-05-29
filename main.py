import asyncio
import aiofiles
import sys # For flushing stdout

async def generate_numbers_for_prefix(writer, prefix_code, total_numbers_to_generate, status_update_interval=200_000):
    """
    Generates subscriber numbers for a given prefix and writes them in various formats.
    The subscriber part is always 7 digits long.
    """
    national_prefix_no_zero = prefix_code[1:]  # e.g., "11" from "011"
    
    lines_buffer = []
    # Buffer 5000 lines (1000 numbers * 5 formats) before each async write operation.
    # This reduces the overhead of frequent small writes.
    write_buffer_size = 5000 

    for i in range(total_numbers_to_generate):  # Generates numbers from 0000000 to 9999999
        subscriber_part_raw = f"{i:07d}" # Ensures 7 digits for subscriber part, e.g., "0000000"
        
        # For readable formats, split the 7-digit subscriber number (e.g., 1234567 -> 123 4567)
        sub1 = subscriber_part_raw[:3]
        sub2 = subscriber_part_raw[3:]
        readable_subscriber_part = f"{sub1} {sub2}" 

        # Format 1: National, no spaces (e.g., 0111234567)
        lines_buffer.append(f"{prefix_code}{subscriber_part_raw}\n")
        # Format 2: National, with spaces (e.g., 011 123 4567)
        lines_buffer.append(f"{prefix_code} {readable_subscriber_part}\n")
        # Format 3: National, with parentheses for prefix (e.g., (011) 123 4567)
        lines_buffer.append(f"({prefix_code}) {readable_subscriber_part}\n")
        
        # Format 4: International, no leading '0', no spaces (e.g., +27111234567)
        lines_buffer.append(f"+27{national_prefix_no_zero}{subscriber_part_raw}\n")
        # Format 5: International, no leading '0', with spaces (e.g., +27 11 123 4567)
        lines_buffer.append(f"+27 {national_prefix_no_zero} {readable_subscriber_part}\n")
        
        if len(lines_buffer) >= write_buffer_size:
            await writer.writelines(lines_buffer)
            lines_buffer.clear()

        if (i + 1) % status_update_interval == 0: # Log progress periodically
             progress_percent = (i + 1) / total_numbers_to_generate * 100
             print(f"Progress for {prefix_code}: {progress_percent:.1f}% ({i+1:,}/{total_numbers_to_generate:,} numbers processed).", flush=True)

    # Write any remaining lines in the buffer after the loop finishes
    if lines_buffer:
        await writer.writelines(lines_buffer)
        lines_buffer.clear()
    

async def main_async_generator():
    # South African numbers are typically 10 digits:
    # Leading '0' + 2-digit prefix code + 7-digit subscriber number.
    # Thus, for each 3-digit prefix (like "011", "082"), there are 10^7 (10 million) possible subscriber numbers.
    total_numbers_per_prefix = 10_000_000 
    
    # This list of prefixes is based on general knowledge of the South African numbering plan.
    # It includes common geographic (landline) prefixes, mobile network prefixes,
    # and some common non-geographic prefixes like VoIP (087) and Toll-Free (080).
    # It aims for comprehensiveness for "standard" 10-digit numbers.
    # Highly specialized prefixes (e.g., premium rate 09x, specific machine-to-machine) are excluded.
    initial_prefixes = [
        # Geographic Prefixes (National Dialling Code 0 + Area Code)
        "010", "011", "012", "013", "014", "015", "016", "017", "018", 
        "021", "022", "023", "024", "027", "028", 
        "031", "032", "033", "034", "035", "036", "039", 
        "040", "041", "042", "043", "044", "045", "046", "047", "048", "049",
        "051", "053", "054", "056", "057", "058", 

        # Mobile Prefixes
        "060", "061", "062", "063", "064", "065", "066", "067", "068", "069",
        "071", "072", "073", "074", "076", "078", "079", 
        
        # Other common Non-Geographic Prefixes
        "080", # Toll-Free
        "081", # Mobile (e.g., Telkom Mobile, Rain)
        "082", # Mobile (Vodacom)
        "083", # Mobile (MTN)
        "084", # Mobile (Cell C)
        "085", # USAL (Under-Serviced Area Licenses)
        "086", # General for ShareCall, MaxiCall, some Value-Added Services (VAS)
        "087", # VoIP services
    ]
    
    # Ensure all prefixes are valid 3-digit codes starting with '0', unique, and sorted.
    final_prefixes = sorted(list(set(p for p in initial_prefixes if len(p) == 3 and p.startswith('0') and p[1:].isdigit())))

    output_filename = "sa_phone_numbers_generated.txt"
    
    num_prefixes = len(final_prefixes)
    formats_per_number = 5 # Each number is written in 5 different formats
    estimated_lines = num_prefixes * total_numbers_per_prefix * formats_per_number
    # Rough estimate for average characters per line (including newline):
    avg_chars_per_line = 16 
    estimated_size_gb = (estimated_lines * avg_chars_per_line) / (1024**3) # Convert bytes to GB
    
    # Configure how often to print progress updates (e.g., 20 times per prefix, or every 5%)
    status_update_interval = total_numbers_per_prefix // 20 

    print("--- South African Phone Number Generator ---", flush=True)
    print(f"This script will generate structurally valid South African phone numbers.", flush=True)
    print(f"Number of unique prefixes to process: {num_prefixes}", flush=True)
    print(f"Full list of prefixes: {', '.join(final_prefixes)}", flush=True)
    print(f"Numbers to generate per prefix: {total_numbers_per_prefix:,}", flush=True)
    print(f"Formats per number: {formats_per_number}", flush=True)
    print(f"Estimated total lines to be written: {estimated_lines:,}", flush=True)
    print(f"Estimated final file size: ~{estimated_size_gb:.2f} GB", flush=True)
    print(f"Output will be saved to: {output_filename}", flush=True)
    print("\nWARNING: This operation will consume significant disk space and take a VERY LONG TIME", flush=True)
    print("(potentially many hours or even days depending on your system).", flush=True)
    print("Ensure you have sufficient free disk space and that your system can run uninterrupted.", flush=True)
    print("It is recommended to run this in a stable environment (e.g., a server or a PC that won't go to sleep).", flush=True)
    
    try:
        # Pause to allow the user to read warnings and cancel if necessary (Ctrl+C).
        print("\nStarting generation in 10 seconds... Press Ctrl+C to cancel.", flush=True)
        await asyncio.sleep(10) 
    except (asyncio.CancelledError, KeyboardInterrupt): 
        print("\nOperation cancelled by user before starting.", flush=True)
        return

    print("\nStarting generation process...\n", flush=True)

    # Open the output file asynchronously.
    # `aiofiles` uses a thread pool for file operations, making writes non-blocking for the asyncio event loop.
    # A larger buffer can improve write performance by reducing system calls.
    async with aiofiles.open(output_filename, mode="w", encoding="utf-8", buffering=65536) as f:
        for prefix_idx, prefix_code in enumerate(final_prefixes):
            print(f"--- Starting prefix {prefix_idx + 1}/{num_prefixes}: {prefix_code} ---", flush=True)
            try:
                await generate_numbers_for_prefix(f, prefix_code, total_numbers_per_prefix, status_update_interval)
                await f.flush() # Ensure all data for the completed prefix is written to disk.
                print(f"--- Finished processing prefix {prefix_idx + 1}/{num_prefixes}: {prefix_code} ---", flush=True)
            except Exception as e_prefix:
                # Log error for the specific prefix and continue with the next one.
                print(f"Error encountered while processing prefix {prefix_code}: {e_prefix}. Skipping to next prefix.", flush=True)
            
            if prefix_idx < num_prefixes - 1:
                 print("Taking a brief pause before processing the next prefix...", flush=True)
                 await asyncio.sleep(2) # Small pause, can be adjusted or removed.

    print(f"\nGeneration task complete. All planned phone numbers have been written to {output_filename}", flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(main_async_generator())
    except KeyboardInterrupt:
        # Handle Ctrl+C interruption gracefully.
        print("\n--- Phone number generation was manually interrupted by the user. ---", flush=True)
    except Exception as e_global:
        # Catch any other unexpected errors during script execution.
        print(f"\n--- An unexpected global error occurred: {e_global} ---", flush=True)
    finally:
        print("--- Script execution has finished. ---", flush=True)
