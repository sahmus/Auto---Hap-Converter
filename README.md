# HAP Batch Converter

A Python desktop app (Tkinter) for converting every video in a folder to the HAP codec using `ffmpeg`.

## Features

- Batch conversion from one folder to another
- Option to use **high-quality HAP** (`hap_q`)
- Output tuned for TouchDesigner compatibility (`rgba`, `snappy`, `chunks=4`)
- Optional audio as uncompressed PCM (disabled by default for faster conversion)
- Live conversion log and progress bar

## Requirements

- Python 3.9+
- `ffmpeg` available on your system `PATH`

## Run

```bash
python hap_batch_converter.py
```

1. Choose a source folder containing videos.
2. Choose an output folder.
3. Toggle:
   - **Use high quality HAP (hap_q)**
   - **Include audio (PCM, slower)**
4. Click **Convert Folder**.

Supported input extensions:
`mp4, mov, mkv, avi, m4v, wmv, webm, mpg, mpeg, flv, mts, m2ts`
