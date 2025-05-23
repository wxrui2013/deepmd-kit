# SPDX-License-Identifier: LGPL-3.0-or-later
from typing import (
    Any,
    Optional,
    Union,
)

import array_api_compat
import numpy as np

from deepmd.dpmodel import (
    DEFAULT_PRECISION,
)
from deepmd.dpmodel.common import (
    cast_precision,
)
from deepmd.dpmodel.fitting.base_fitting import (
    BaseFitting,
)
from deepmd.dpmodel.output_def import (
    FittingOutputDef,
    OutputVariableDef,
    fitting_check_output,
)
from deepmd.utils.version import (
    check_version_compatibility,
)

from .general_fitting import (
    GeneralFitting,
)


@BaseFitting.register("dipole")
@fitting_check_output
class DipoleFitting(GeneralFitting):
    r"""Fitting rotationally equivariant diploe of the system.

    Parameters
    ----------
    ntypes
            The number of atom types.
    dim_descrpt
            The dimension of the input descriptor.
    embedding_width : int
        The dimension of rotation matrix, m1.
    neuron
            Number of neurons :math:`N` in each hidden layer of the fitting net
    resnet_dt
            Time-step `dt` in the resnet construction:
            :math:`y = x + dt * \phi (Wx + b)`
    numb_fparam
            Number of frame parameter
    numb_aparam
            Number of atomic parameter
    rcond
            The condition number for the regression of atomic energy.
    tot_ener_zero
            Force the total energy to zero. Useful for the charge fitting.
    trainable
            If the weights of fitting net are trainable.
            Suppose that we have :math:`N_l` hidden layers in the fitting net,
            this list is of length :math:`N_l + 1`, specifying if the hidden layers and the output layer are trainable.
    activation_function
            The activation function :math:`\boldsymbol{\phi}` in the embedding net. Supported options are |ACTIVATION_FN|
    precision
            The precision of the embedding net parameters. Supported options are |PRECISION|
    layer_name : list[Optional[str]], optional
            The name of the each layer. If two layers, either in the same fitting or different fittings,
            have the same name, they will share the same neural network parameters.
    use_aparam_as_mask: bool, optional
            If True, the atomic parameters will be used as a mask that determines the atom is real/virtual.
            And the aparam will not be used as the atomic parameters for embedding.
    mixed_types
            If true, use a uniform fitting net for all atom types, otherwise use
            different fitting nets for different atom types.
    exclude_types
            Atomic contributions of the excluded atom types are set zero.
    r_differentiable
            If the variable is differentiated with respect to coordinates of atoms.
            Only reducible variable are differentiable.
    c_differentiable
            If the variable is differentiated with respect to the cell tensor (pbc case).
            Only reducible variable are differentiable.
    type_map: list[str], Optional
            A list of strings. Give the name to each type of atoms.
    """

    def __init__(
        self,
        ntypes: int,
        dim_descrpt: int,
        embedding_width: int,
        neuron: list[int] = [120, 120, 120],
        resnet_dt: bool = True,
        numb_fparam: int = 0,
        numb_aparam: int = 0,
        rcond: Optional[float] = None,
        tot_ener_zero: bool = False,
        trainable: Optional[list[bool]] = None,
        activation_function: str = "tanh",
        precision: str = DEFAULT_PRECISION,
        layer_name: Optional[list[Optional[str]]] = None,
        use_aparam_as_mask: bool = False,
        spin: Any = None,
        mixed_types: bool = False,
        exclude_types: list[int] = [],
        r_differentiable: bool = True,
        c_differentiable: bool = True,
        type_map: Optional[list[str]] = None,
        seed: Optional[Union[int, list[int]]] = None,
    ) -> None:
        if tot_ener_zero:
            raise NotImplementedError("tot_ener_zero is not implemented")
        if spin is not None:
            raise NotImplementedError("spin is not implemented")
        if use_aparam_as_mask:
            raise NotImplementedError("use_aparam_as_mask is not implemented")
        if layer_name is not None:
            raise NotImplementedError("layer_name is not implemented")

        self.embedding_width = embedding_width
        self.r_differentiable = r_differentiable
        self.c_differentiable = c_differentiable
        super().__init__(
            var_name="dipole",
            ntypes=ntypes,
            dim_descrpt=dim_descrpt,
            neuron=neuron,
            resnet_dt=resnet_dt,
            numb_fparam=numb_fparam,
            numb_aparam=numb_aparam,
            rcond=rcond,
            tot_ener_zero=tot_ener_zero,
            trainable=trainable,
            activation_function=activation_function,
            precision=precision,
            layer_name=layer_name,
            use_aparam_as_mask=use_aparam_as_mask,
            spin=spin,
            mixed_types=mixed_types,
            exclude_types=exclude_types,
            type_map=type_map,
            seed=seed,
        )

    def _net_out_dim(self):
        """Set the FittingNet output dim."""
        return self.embedding_width

    def serialize(self) -> dict:
        data = super().serialize()
        data["type"] = "dipole"
        data["embedding_width"] = self.embedding_width
        data["r_differentiable"] = self.r_differentiable
        data["c_differentiable"] = self.c_differentiable
        return data

    @classmethod
    def deserialize(cls, data: dict) -> "GeneralFitting":
        data = data.copy()
        check_version_compatibility(data.pop("@version", 1), 2, 1)
        var_name = data.pop("var_name", None)
        assert var_name == "dipole"
        return super().deserialize(data)

    def output_def(self):
        return FittingOutputDef(
            [
                OutputVariableDef(
                    self.var_name,
                    [3],
                    reducible=True,
                    r_differentiable=self.r_differentiable,
                    c_differentiable=self.c_differentiable,
                ),
            ]
        )

    @cast_precision
    def call(
        self,
        descriptor: np.ndarray,
        atype: np.ndarray,
        gr: Optional[np.ndarray] = None,
        g2: Optional[np.ndarray] = None,
        h2: Optional[np.ndarray] = None,
        fparam: Optional[np.ndarray] = None,
        aparam: Optional[np.ndarray] = None,
    ) -> dict[str, np.ndarray]:
        """Calculate the fitting.

        Parameters
        ----------
        descriptor
            input descriptor. shape: nf x nloc x nd
        atype
            the atom type. shape: nf x nloc
        gr
            The rotationally equivariant and permutationally invariant single particle
            representation. shape: nf x nloc x ng x 3
        g2
            The rotationally invariant pair-partical representation.
            shape: nf x nloc x nnei x ng
        h2
            The rotationally equivariant pair-partical representation.
            shape: nf x nloc x nnei x 3
        fparam
            The frame parameter. shape: nf x nfp. nfp being `numb_fparam`
        aparam
            The atomic parameter. shape: nf x nloc x nap. nap being `numb_aparam`

        """
        xp = array_api_compat.array_namespace(descriptor, atype)
        nframes, nloc, _ = descriptor.shape
        assert gr is not None, "Must provide the rotation matrix for dipole fitting."
        # (nframes, nloc, m1)
        out = self._call_common(descriptor, atype, gr, g2, h2, fparam, aparam)[
            self.var_name
        ]
        # (nframes * nloc, 1, m1)
        out = xp.reshape(out, (-1, 1, self.embedding_width))
        # (nframes * nloc, m1, 3)
        gr = xp.reshape(gr, (nframes * nloc, -1, 3))
        # (nframes, nloc, 3)
        # out = np.einsum("bim,bmj->bij", out, gr).squeeze(-2).reshape(nframes, nloc, 3)
        out = out @ gr
        out = xp.reshape(out, (nframes, nloc, 3))
        return {self.var_name: out}
