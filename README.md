# octorag
Lightweight agent that uses GitHub Search API to do RAG for tasks such as recommending projects and libraries, and generating code with its selections. Written in Python using LangGraph.

## Dependencies
- `httpx`
- `langchain`
- `langgraph`
- `python-dotenv`
- `typing_extensions`

You can install these using the `requirements.txt` file in the root directory. This would be `pip install -r requirements.txt` if using pip from the root directory.

## Usage
OctoRAG can be called as a library, or be run as a command-line application. Either way, you need to either have a `.env` file inside this folder (if run as a Python application) or at a location passed to OctoRAG when initializing (if called as a library). *Or*, you should have the following environment variables set beforehand. 
- `ANTHROPIC_API_KEY`: Your Anthropic Console API key, required to query the Anthropic model.
- `GH_ACCESS_TOKEN`: A GitHub access token. GitHub has less strict rate limiting on authenticated requests, so this allows for more informed predictions.

### As a Library
Instantiate OctoRAG using the following:
```
from octorag import OctoRAG

model = OctoRAG("path/to/env/file") # Looks for a .env file in the root directory by default
```

And query the model using the `query` method:

```
>>> model.query("I need an open-source raytracer for a bigger project I'm working on. It needs to be able to be called as a library, like I can just call a `raytrace()` function and it draws the input scene for me. I'm working in Rust. Give me a single up-to-date recommendations.")
Based on my research, I recommend **embree-rs** as your best option for a raytracer library in Rust. Here's why:

## Recommendation: embree-rs

**GitHub Repository**: [https://github.com/Twinklebear/embree-rs](https://github.com/Twinklebear/embree-rs)  
**Crates.io**: [https://crates.io/crates/embree](https://crates.io/crates/embree)

### Key Features:
1. **Production-Ready**: Embree is Intel's high-performance ray tracing kernels, widely used in professional rendering software.
2. **Library Interface**: Can be used as a Rust library with a clean API for creating and rendering scenes.
3. **Well-Maintained**: Has active development with the latest update relatively recent.
4. **Comprehensive Documentation**: Documentation available on docs.rs and several examples showing how to use it.
5. **High Performance**: Leverages SIMD instructions for extremely fast ray tracing.
6. **Advanced Features**: Supports various geometry types (triangles, quads, curves), instancing, and parallel ray tracing.

### Integration:
1. Add to your Cargo.toml:
   ```toml
   [dependencies]
   embree = "0.3.8"
   cgmath = "0.18"  # For vector math
   \```

2. Basic usage pattern:
   ```rust
   use embree::{Device, Scene, TriangleMesh, Geometry, IntersectContext, Ray, RayHit};
   use cgmath::{Vector3, Vector4};
   
   // Create a device
   let device = Device::new();
   
   // Create geometry (e.g., a triangle mesh)
   let mut triangle_mesh = TriangleMesh::unanimated(&device, triangle_count, vertex_count);
   // Fill vertex and index buffers...
   
   // Create a geometry object and commit it
   let mut geometry = Geometry::Triangle(triangle_mesh);
   geometry.commit();
   
   // Create and build a scene
   let mut scene = Scene::new(&device);
   scene.attach_geometry(geometry);
   let rtscene = scene.commit();
   
   // Create intersection context
   let mut context = IntersectContext::coherent();
   
   // For each pixel, create a ray and trace it
   let mut ray_hit = RayHit::new(
       Ray::new(origin, direction, 0.0, f32::INFINITY),
   );
   rtscene.intersect(&mut context, &mut ray_hit);
   
   // Check if something was hit and process the result
   if ray_hit.hit.hit() {
       // Get hit information and color the pixel
   }
   \```

This library gives you a powerful, fast raytracer that can be called from your Rust code, which matches your requirement of being able to use it as a library and call a function to render a scene.
```

### As a Python application
Install the OctoRag application using `pip install .` in the root directory. From there, you can query OctoRAG simply by entering `octorag` in the command line!