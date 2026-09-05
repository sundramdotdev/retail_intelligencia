# Engineering Portfolio

## Overview
A public-facing, separate Next.js application designed to showcase the architectural depth, system design, and engineering philosophy behind the developer's work.

## Design System
*   **Aesthetic**: Dark, editorial, minimalist. "A system that communicates state, not marketing slogans."
*   **Typography**: 
    *   *Display*: Space Grotesk
    *   *Body*: Inter
    *   *Monospace*: JetBrains Mono
*   **Palette**: Deep blacks (`#080808`, `#0D0D0D`), subtle grays, and a distinct bronze/amber accent (`#C18A42`).

## Architecture
Built as a static-ready Next.js application using the App Router and Tailwind CSS v4.
*   `/`: Hero introduction and featured work.
*   `/work`: Full list of engineering projects.
*   `/work/[slug]`: Deep-dive architectural case studies (e.g., Retail Intelligencia).
*   `/about`: Engineering philosophy and capabilities.
*   `/contact`: Communication links.

## Content (Retail Intelligencia Case Study)
The primary case study breaks down the hackathon project into 5 core engineering tenets:
1.  **The Problem Space**: Why physical retail observability is difficult.
2.  **Hardware-First Architecture**: Why video shouldn't be streamed to the cloud (bandwidth, compute, privacy).
3.  **Privacy by Design**: Bounding boxes, ephemeral IDs, and zero facial recognition.
4.  **Deterministic Intelligence**: Ray-casting and strict operational thresholds instead of generative LLMs.
5.  **Closing the Loop**: The SSE dashboard and staff action system.

## Configuration
It runs on port `3001` (to avoid conflicting with the Dashboard on `3000`) and builds as a Next.js `standalone` app for Docker Compose deployment.
