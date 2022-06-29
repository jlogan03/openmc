import numpy as np
import pytest
import vtk
from os.path import exists

import openmc


def test_xml_roundtrip(run_in_tmpdir):
    # Create a tally with all possible gizmos
    mesh = openmc.RegularMesh()
    mesh.lower_left = (-10., -10., -10.)
    mesh.upper_right = (10., 10., 10.,)
    mesh.dimension = (5, 5, 5)
    mesh_filter = openmc.MeshFilter(mesh)
    tally = openmc.Tally()
    tally.filters = [mesh_filter]
    tally.nuclides = ['U235', 'I135', 'Li6']
    tally.scores = ['total', 'fission', 'heating']
    tally.derivative = openmc.TallyDerivative(
        variable='nuclide_density', material=1, nuclide='Li6'
    )
    tally.triggers = [openmc.Trigger('rel_err', 0.025)]
    tally.triggers[0].scores = ['total', 'fission']
    tallies = openmc.Tallies([tally])

    # Roundtrip through XML and make sure we get what we started with
    tallies.export_to_xml()
    new_tallies = openmc.Tallies.from_xml()
    assert len(new_tallies) == 1
    new_tally = new_tallies[0]
    assert new_tally.id == tally.id
    assert len(new_tally.filters) == 1
    assert isinstance(new_tally.filters[0], openmc.MeshFilter)
    assert np.allclose(new_tally.filters[0].mesh.lower_left, mesh.lower_left)
    assert new_tally.nuclides == tally.nuclides
    assert new_tally.scores == tally.scores
    assert new_tally.derivative.variable == tally.derivative.variable
    assert new_tally.derivative.material == tally.derivative.material
    assert new_tally.derivative.nuclide == tally.derivative.nuclide
    assert len(new_tally.triggers) == 1
    assert new_tally.triggers[0].trigger_type == tally.triggers[0].trigger_type
    assert new_tally.triggers[0].threshold == tally.triggers[0].threshold
    assert new_tally.triggers[0].scores == tally.triggers[0].scores


cylinder_mesh = openmc.CylindricalMesh()
cylinder_mesh.r_grid = np.linspace(1, 2, num=30)
cylinder_mesh.phi_grid = np.linspace(0, np.pi / 2, num=50)
cylinder_mesh.z_grid = np.linspace(0, 1, num=30)

regular_mesh = openmc.RegularMesh()
regular_mesh.lower_left = [0, 0, 0]
regular_mesh.upper_right = [1, 1, 1]
regular_mesh.dimension = [10, 5, 6]

rectilinear_mesh = openmc.RectilinearMesh()
rectilinear_mesh.x_grid = np.linspace(0, 1)
rectilinear_mesh.y_grid = np.linspace(0, 1)
rectilinear_mesh.z_grid = np.linspace(0, 1)


@pytest.mark.parametrize("mesh", [cylinder_mesh, regular_mesh, rectilinear_mesh])
def test_voxels_to_vtk(mesh):
    vtk_grid = openmc.voxels_to_vtk(mesh, mean=None, std_dev=None)
    assert isinstance(vtk_grid, vtk.vtkStructuredGrid)


@pytest.mark.parametrize("mesh", [cylinder_mesh, regular_mesh, rectilinear_mesh])
def test_write_to_vtk(mesh, tmpdir):
    # build
    tally = openmc.Tally()
    tally.filters = [openmc.MeshFilter(mesh)]
    filename = tmpdir / "out.vtk"
    # run
    tally.write_to_vtk(filename)
    # test
    assert exists(filename)


def test_write_to_vtk_raises_error_when_no_meshfilter():
    # build
    tally = openmc.Tally()

    # test
    expected_err_msg = "write_to_vtk requires a MeshFilter in the tally filters"
    with pytest.raises(ValueError, match=expected_err_msg):
        tally.write_to_vtk("out.vtk")


def test_voxel_to_vtk_raises_error_with_wrong_mesh():
    # build
    tally = openmc.Tally()
    spherical_mesh = openmc.SphericalMesh()
    spherical_mesh.r_grid = np.linspace(1, 2)
    spherical_mesh.phi_grid = np.linspace(1, 2)
    spherical_mesh.theta_grid = np.linspace(1, 2)
    tally.filters = [openmc.MeshFilter(spherical_mesh)]
    # test
    expected_err_msg = "voxels_to_vtk only works with openmc.RegularMesh, openmc.RectilinearMesh, openmc.CylindricalMesh"
    with pytest.raises(ValueError, match=expected_err_msg):
        tally.write_to_vtk("out.vtk")