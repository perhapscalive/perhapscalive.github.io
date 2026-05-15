# SWESolver-1D: A High-Performance Solver for Complex 1D River Network Hydrodynamics

**Author:** Penghan Chen

*A fully self-developed C++ 1D river network hydrodynamic model, heavily inspired by the conservative Finite Volume Method (FVM) theory of Ying et al., and the river network junction (bifurcation) treatment method of Li et al. The model employs a cell-centered finite volume method, supports arbitrary irregular cross-section shapes, utilizes the HLL approximate Riemann solver with robust wetting and drying boundary handling, and leverages OpenMP for multi-threaded high-performance CPU parallel computing.*

> **Research Vision & Value:** 
> Building a complete 1D river network hydrodynamic core solver from scratch ensures absolute control over every line of the underlying code, and provides immense flexibility for future integration of complex hydraulic structures (e.g., gates, pump stations), sediment transport, and water quality modules. Unlike closed-source commercial software, the transparent architecture of this model allows for deep customization and coupling of numerical schemes, non-linear conservation equations at junctions, and hardware acceleration strategies.

## Governing Equations

The model solves the 1D shallow water equations (Saint-Venant equations). Following Ying et al., to naturally handle irregular cross-sections and maintain the well-balanced property, the momentum equation is formulated using the water surface gradient form instead of the hydrostatic pressure integral form:

Conserved variables vector $U = (A, Q)^T$, where $A$ is the cross-sectional area and $Q$ is the discharge.

$$
\frac{\partial A}{\partial t} + \frac{\partial Q}{\partial x} = S_m
$$

$$
\frac{\partial Q}{\partial t} + \frac{\partial}{\partial x}\left(\frac{Q^2}{A}\right) + g A \frac{\partial Z}{\partial x} = - g A S_f
$$

This can be written in a compact weakly-conservative vector form:

$$
\frac{\partial U}{\partial t} + \frac{\partial F(U)}{\partial x} = S(U, Z)
$$

Where the advective flux $F$ and the source term $S$ are defined as:

$$
F = \begin{bmatrix} Q \\ \frac{Q^2}{A} \end{bmatrix}, \quad S = \begin{bmatrix} S_m \\ -gA\frac{\partial Z}{\partial x} - g A S_f \end{bmatrix}
$$

*(Note: The pressure gradient is treated as a topographic source term $\mathbf{S_b = -g A \frac{\partial Z}{\partial x}}$. It evaluates the water surface elevation $Z$ across cell interfaces to perfectly balance static water bodies over irregular beds without needing complex integral treatments.)*

The bottom friction is evaluated semi-implicitly to prevent flow reversal within a single time step:

$$
g A S_f = \frac{g n^2 |Q| Q}{A R^{4/3}}
$$

## Core Numerical Method 

To ensure mass conservation, shock-capturing capability, and adaptability to complex natural rivers, the solver utilizes well-established numerical schemes:

- **Finite Volume Method (FVM):** Spatial discretization is performed on control volume cell grids, independently calculating mass and momentum fluxes for each river reach.
- **HLL Riemann Solver:** The numerical flux at control volume interfaces is computed using the HLL (Harten-Lax-van Leer) approximate Riemann solver, accurately capturing surge waves and handling wet-dry flow advancement. Wave speeds are estimated, and fluxes are limited based on Roe-averaged wave speeds.
- **Pre-processed Irregular Cross-Sections (Lookup Tables):** For natural riverbeds, topographic cross-sections are pre-processed into property lookup tables containing 200 water level segments. During the computation loop, surface width $B$, wetted perimeter $P$, and area $A$ are rapidly obtained via Lagrange/linear interpolation.
- **Time Advancing & CFL Control:** Adaptive time step regulation combined with the CFL condition: $\Delta t = \text{CFL} \cdot \min \left( \frac{\Delta x}{|V| + \sqrt{g h_{avg}}} \right)$. A predictor-corrector scheme (RK2-like) is adopted, balancing computational efficiency and second-order time accuracy.

## River Network Junction (Bifurcation point) Coupling 

For tree/net-like and reticular junctions in complex river networks, the model discards the simple fully-implicit large matrix solving method. Instead, it adopts an explicit time-marching water level update based on strict mass conservation:

**Junction Mass Equation:**
$$
A_{bp} \frac{d Z_{bp}}{dt} = \sum Q_{in} - \sum Q_{out} = Q_{net}
$$

**Coupling Core within a Time Step:**
1. **Boundary Condition Coordination:** The computational boundary water level of all adjacent river reaches (Ghost Cells) connected to the current junction is forcibly set to the unified water level of the confluence point $Z_{bp}$.
2. **Net Flux Calculation:** Calculate the HLL flux for states on both sides of the interface, and sum the inward inflowing fluxes to obtain the net discharge $Q_{net}$.
3. **Water Level Evolution Update:** Uses explicit integration to update the junction water level at the new time step. Because the virtual storage area of the node is defined as $A_{bp} = \beta L \bar{B}$ ($\beta$ is an empirical coefficient), this method maintains excellent convergence capability in highly complex unstructured water networks while avoiding the assembly of exceptionally large sparse matrices.

## Hardware Parallel Acceleration

To address large-scale, long-term simulations of highly detailed basin river networks, the model implements system-level data concurrency strategies:

- **OpenMP CPU Concurrency:** Employs block-scheduling-based `#pragma omp parallel for` statements in data-independent, dense computational loops (embarrassingly parallel loops) — such as cross-section interpolation, control volume state reconstruction, Riemann solvers, and source term computations — to fully extract multi-core processing power.
- **Optimized Storage Design:** 1D data structures use contiguous dynamic arrays (`std::vector`) to manage original independent field variables, providing perfect CPU Cache-friendly iteration performance.

## Architecture and Key Modules

- **RiverNet:** The global large topology container, responsible for managing all mutually independent `River` objects and executing `BifurPoints` junction iterative coupling computations.
- **River:** The hydrodynamic computing carrier for a single river reach/mainstream, maintaining its own $A, Q, Z, B$ conservation variables alongside derived intermediate fields.
- **BifurPoints:** The confluence node manager, governing the topological queries connecting each river reach and storing/updating storage water volumes and levels.
- **CSShape:** The cross-section geometric interpolator, abstracting complex polygon intersection calculations to directly output the current water surface characteristics and hydraulic radius.
- **Gates:** Provides a structured internal boundary interception module, supporting calculations for discharge-controlled flow through gates (e.g., dispatch rules based on FLX_GATE).
- **BoundaryCondition & PointSource:** External boundary and distributed point source systems seamlessly docking with transient forcings or gauge station curves through time interpolation mechanisms.

**Core Tech Stack:** `CMake` | `C++17` | `STL` | `OpenMP` | `spdlog`

## Control Flow and Computation Loop

1. **Read Project Files:** Load river reach network, node topology, cross-section attributes, external boundaries, and time series arrays.
2. **Pre-processing and Topology Construction:** Build adjacency lists based on junction points; bake interpolation property tables (1D Lookup array) for all cross-sections.
3. **Initialization:** Assign initial steady-state water level/discharge values to the entire basin or individual river reaches.
4. **Advance Main Loop (`Solver::solve()`):**
   - Determine the minimum safe time step $\Delta t$ driven by CFL conditions across all river reaches.
   - Update conditional interpolation for external water boundaries.
   - Propagate junction water levels to connected river reach extremities.
   - **(Computation Core)** Solve HLL cell fluxes and source term variations for all river reaches (incorporating multi-threading acceleration).
   - Complete the integral evolution of conservative variables $U^{n+1}$ and the derived restoration of water depths/surface elevations.
   - Iteratively update the water level changes driven by mass differences at network junctions.
5. **Output Writing:** Trigger chronological output of global state arrays, interfacing perfectly with customized Python spatiotemporal slice plots and data analysis tools.

## Contributions and Future Roadmap

This 1D solver possesses a high degree of robustness and modular independence. Upcoming key developments primarily include:
- Supporting the full integration of dynamic dam and pump station dispatch rules alongside weir flow coupling.
- Achieving **lateral seamless 1D-2D dynamic nesting** with the existing 2D areal model (SWESolver-2D) for refined, high-precision simulations of urban flood inundation or mountain levee overtopping.
- Incorporating concomitant sediment conservation/transport components and an eutrophication/biochemical equation library.

---
*© 2026 Penghan Chen. SWESolver-1D Academic Poster - River Network Dynamics.*