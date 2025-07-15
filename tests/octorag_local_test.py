from octorag.octorag import OctoRAG

model = OctoRAG()

q = model.query(
    "I need an open-source raytracer for a bigger project I'm working on. It needs to be able to be called as a library, like I can just call a `raytrace()` function and it draws the input scene for me. I'm working in Rust. Give me a single up-to-date recommendations."
)

print(q)
