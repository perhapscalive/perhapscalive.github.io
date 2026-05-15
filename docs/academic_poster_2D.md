# SWESolver: An Extensible Solver for Two-Dimensional Shallow-Water Dynamics

**Author:** Penghan Chen

*A self-developed C++ hydrodynamic model reproducing established academic numerical techniques for shallow-water equations. It focuses on cell-centered finite volume methods on unstructured triangular meshes, HLLC shock-capturing, robust wetting-drying schemes, and high-performance execution using both CPU (OpenMP) and GPU (CUDA).*

> **Research Vision & Value:** 
> Mastering the full-stack, independent development of a core hydrodynamic solver unlocks immense potential for advanced research in hydrodynamics, large-scale hydrology, and Earth system modeling. By building the model entirely from scratch, it guarantees transparent access to every internal component—enabling flexible, granular modifications to numerical schemes, physical processes, and hardware kernels that closed-source or legacy software simply cannot accommodate.

## Project Snapshot
- C++17 core & OpenMP CPU backend
- Optional CUDA kernels
- Custom / MIKE21 / Guiren mesh readers
- Standalone text-based project I/O

---

## Governing Equations

The model solves the depth-averaged shallow-water equations in conservative variables $U = (h, q_x, q_y)^T$, where $h$ is water depth and $q_x, q_y$ are unit-width discharges.

$$
\frac{\partial U}{\partial t} + \frac{\partial F(U)}{\partial x} + \frac{\partial G(U)}{\partial y} = S_b + S_f + S_m
$$
*Bed slope, Manning friction, and mass source terms are handled explicitly or semi-implicitly.*

$$
F = \left(q_x, \frac{q_x^2}{h} + \frac{gh^2}{2}, \frac{q_xq_y}{h}\right)^T, \quad G = \left(q_y, \frac{q_xq_y}{h}, \frac{q_y^2}{h} + \frac{gh^2}{2}\right)^T
$$

$$
S_{f,x} = - \frac{g n^2 u \sqrt{u^2+v^2}}{h^{1/3}}, \quad S_{f,y} = - \frac{g n^2 v \sqrt{u^2+v^2}}{h^{1/3}}
$$
*A semi-implicit limiter prevents friction from reversing discharge in one time step.*

## Numerical Method

The solver implements well-established numerical techniques to ensure mass conservation, stability, and accurate shock-capturing:

- **Finite Volume Method (FVM):** Cell-centered spatial discretization on unstructured triangular grids, adaptable to complex real-world topographies.
- **Riemann Solver:** Edge-normal numerical fluxes are computed using the HLLC (Harten-Lax-van Leer-Contact) approximate Riemann solver, correctly capturing shock waves and dry-bed advancing fronts.
- **Wetting & Drying Scheme:** Uses hydrostatic reconstruction with local bed elevation to prevent negative water depths and spurious velocities in extremely shallow areas.
- **Time Marching:** Explicit second-order Runge-Kutta (RK2) time integration coupled with an adaptive CFL-controlled time step: $\Delta t = \text{CFL} \cdot \min(r_i / (|u| + \sqrt{gh}))$.
- **Source Term Treatment:** Semi-implicit discretization of bottom friction for steady stability, alongside centered discretization for bed slopes.

## Parallel Acceleration

To accelerate large-scale simulations on dense unstructured meshes, the solver implements a dual-backend hardware approach mapping directly to the underlying physical algorithms:

- **CPU Multi-threading:** Leverages OpenMP parallel loops across spatial cell and edge iterations, highly effective for mid-scale domains or headless compute nodes.
- **GPU Computing:** Features a complete CUDA backend converting data into Structure-of-Arrays (SoA) layout to maximize memory coalescing. Custom kernels cover time stepping, flux reconstruction, and bed condition evaluation.

**Metrics & Features:**
- **SoA Layout:** Coalesced GPU device memory
- **C++17 Base:** Modern standard core
- **Zero-copy:** Mapped CPU-GPU synchronization

**CUDA Kernel Example (from `CudaKernels.cu`):**
```cuda
__global__ void fix_negative_h_kernel(real* h, real* qx, real* qy, real* z, real* b, int nc) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    if (idx < nc) {
        if (h[idx] < 0.0) {
            h[idx] = 0.0;
            qx[idx] = 0.0;
            qy[idx] = 0.0;
            z[idx] = b[idx] + h[idx];
        }
    }
}
```

## Implementation Architecture

- **Mesh:** Topology, edge normals, cell areas, node-cell weights, and boundary tags.
- **FieldManager:** Water depth, discharge, reconstructed edge states, fluxes, and source terms.
- **BoundaryCondition:** Solid, free-open, discharge, depth, and water-level boundary forcing.
- **PointSource:** Static or time-varying local inflow mapped to containing mesh cells.
- **TimeIntegrator:** Adaptive or fixed time stepping, observation schedule, and CFL control.
- **Writer:** Mesh export and time-indexed field outputs for post-processing.

**Tech Stack:** `CMake` | `C++17` | `STL` | `OpenMP` | `CUDA optional` | `spdlog` | `Gmsh`

## Simulation Workflow

1. **Read project inputs:** Configuration, mesh, topography, boundary table, point sources, and time series.
2. **Build mesh topology:** Cell-edge-cell connectivity, normals, areas, local signs, and interpolation weights.
3. **Initialize fields:** Water depth or water level, discharge, bottom elevation, and dry-cell thresholds.
4. **Advance SWE state:** Friction, flux reconstruction, convection, slope source, RK2 update, and wet-dry correction.
5. **Export snapshots:** Cell-wise $h, q_x, q_y$ fields at observation times.

**Core Time-Marching Loop (from `Solver::solve()`):**
```cpp
while (!ti->is_end()) 
{   
    // --- Determine Time Step ---
    double adt = phys->compute_adaptive_dt(ti->cfl_number);
    ti->set_time_step(adt);
    
    // --- RK2 Stage 1 (Predictor) ---
    phys->source_friction();
    phys->update_Q_and_z();        // Save h^n
    phys->reconstruction();        // Edge variable extrapolation
    phys->convection();            // HLLC fluxes
    phys->source_slope();          // Bed slope source
    phys->update_Qs_and_z();       // Advance to h^*
    
    // --- RK2 Stage 2 (Corrector) ---
    phys->reconstruction();
    phys->convection();
    phys->source_slope();
    phys->update_Q_by_RK2();       // Advance to h^{n+1}

    // --- State Finalization ---
    phys->update_for_next();       // h, qx, qy variable copy
    phys->source_mass();           // Point sources
    phys->fix_negative_h();        // Guarantee positivity
    
    ti->time_increment();
    bc->update_values(ti->get_time_now());
    ps->update_values(ti->get_time_now());
    
    // Output scheduling handled outside main physics...
}
```

## Boundary & Source Capabilities

- Wall boundaries impose zero mass flux with pressure momentum flux.
- Discharge boundaries distribute prescribed total $Q$ by owned boundary length.
- Water-depth and water-level boundaries use characteristic-style exterior states.
- Time-varying forcing is interpolated from external time-series tables.
- Point sources add mass directly to the located cell each time step.

$$
h^{n+1}_c = h^n_c + \Delta t \cdot s_c
$$
*Project point-source values are mapped from coordinates to mesh cells during preprocessing.*

## Benchmark & Validation Scenarios

The numerical model has been verified against standard analytical solutions and laboratory-scale flow experiments to ensure its computational reliability across different flow regimes:

| Validation Case | Test Objective & Key Features |
| :--- | :--- |
| **Monai Valley Experiment** | Simulates highly complex topography and rapid advancing fronts to validate the generalized wetting-drying scheme. |
| **Dam-break Flow Setup** | Focuses on the HLLC Riemann solver's ability to capture discontinuities and transient shock wave propagation accurately. |
| **Idealized Circular Basin** | Verifies multidirectional symmetry preservation over an unstructured domain and stable boundary condition reflection. |
| **Steady River Reach** | Tests steady-state convergence, semi-implicit bottom friction handling, and complex boundary forcing couplings. |

*Simulations demonstrate robust mass conservation properties and seamless transition between wet and dry domains without sub-grid instability.*

## Data Pipeline & Toolchain

Designed as a highly extensible standalone computational engine, the solver workflow emphasizes transparent data I/O and easy integration with external toolchains:

- **Mesh Support:** Built-in lightweight parsers capable of interpreting generic custom ASCII grids, MIKE 21 structured sets, and standard Guiren mesh topologies.
- **Lightweight Custom I/O:** Implements zero-dependency text-based result outputs optimized for quick inspection and streamlined post-processing.
- **Visualization Ecosystem:** Fully integrated with companion Python visualization scripts and a customized browser-based 3D terrain viewer to interactively query hydrodynamic fields.

## Contributions and Next Steps

- **Robustness:** Wet-dry thresholding, non-negative depth correction, and hydrostatic edge regulation.
- **Extensibility:** Modular components for mesh readers, forcing, physical fields, solver loop, and output.
- **Performance:** OpenMP baseline with CUDA kernels for local flux/source operations and adaptive time-step reduction.

*Planned research-grade additions: automated benchmark reports, conservation diagnostics, double-precision build option, spatially varying Manning support, and reproducible CPU/GPU performance tables.*

---
*© 2026 Penghan Chen. SWESolver Academic Poster - Finite Volume Dynamics.*
