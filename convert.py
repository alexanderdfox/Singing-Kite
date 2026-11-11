import numpy as np
import soundfile as sf
import sys

def parse_obj(filename):
    """Parses an OBJ file and yields 3D vertices one by one to save memory."""
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('v '):
                parts = line.strip().split()
                try:
                    yield [float(parts[1]), float(parts[2]), float(parts[3])]
                except (ValueError, IndexError):
                    continue

def obj_to_audio(obj_path, output_ogg_path, sample_rate=44100, duration_per_vertex=0.04):
    """Converts OBJ vertices into a sequence of sine wave tones and streams them to OGG."""
    
    # First pass: quickly find min and max Y coordinates for normalization
    print(f"Scanning {obj_path} for Y-bounds...")
    y_min, y_max = float('inf'), float('-inf')
    vertex_count = 0
    
    # We'll store vertices in a temporary memory-mapped file or pass through a quick generator
    # For bounds checking, we can just stream through
    for v in parse_obj(obj_path):
        y = v[1]
        if y < y_min: y_min = y
        if y > y_max: y_max = y
        vertex_count += 1

    if vertex_count == 0:
        print("Error: No vertices found in the OBJ file.")
        return

    if y_max == y_min:
        y_max += 1e-5  # Prevent division by zero

    print(f"Found {vertex_count} vertices. Streaming audio directly to {output_ogg_path}...")

    num_samples = int(sample_rate * duration_per_vertex)
    t = np.linspace(0, duration_per_vertex, num_samples, endpoint=False)
    envelope = 0.5 * (1 - np.cos(2 * np.pi * np.arange(num_samples) / num_samples))

    # Open soundfile for writing in streaming mode
    with sf.SoundFile(output_ogg_path, mode='w', samplerate=sample_rate, 
                      channels=1, format='OGG', subtype='VORBIS') as file:
        
        for v in parse_obj(obj_path):
            y = v[1]
            # Map Y coordinate to frequency (150 Hz to 2500 Hz)
            freq = 150 + (y - y_min) / (y_max - y_min) * 2350
            
            # Generate chunk
            wave_chunk = np.sin(2 * np.pi * freq * t) * envelope
            
            # Write chunk immediately to disk (keeps RAM usage minimal)
            file.write(wave_chunk)

    print(f"Success! Audio saved to {output_ogg_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert.py <input.obj> <output.ogg>")
    else:
        obj_to_audio(sys.argv[1], sys.argv[2])