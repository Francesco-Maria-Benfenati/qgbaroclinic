import numpy as np


class EoS:
    """
    This class is for computing the Seawater Equation of State and related variables.
    """

    @staticmethod
    def compute_density(sal: float, pot_temp: float, ref_press: float = 0) -> float:
        """
        Compute density from salinity and potential temperature.

        NOTE: pressure is expressed in dbar.

        Arguments
        ---------
        pot_temp : <numpy.ndarray>
            sea water potential temperature [°C]
        sal : <numpy.ndarray>
            sea water salinity [PSU]
        ref_press : <numpy.ndarray>
            reference pressure in [dbars]. Default to 0

        Raise
        ------
        ValueError if pot_temp and sal has different shapes

        Returns
        -------
        density : <numpy.ndarray>
            density [kg/(m^3)]


        The Eq. Of Seawater used is the one implemented in NEMO:

            rho(sal, temp, p) = rho(sal, temp, 0)/[1 - p/K(sal, temp, p)] ;

        where rho(sal, temp, 0) is a 15-term eq. in powers of sal and temp.
        K(sal, temp, p) is the secant bulk modulus of seawater: a 26-term eq.
        in powers of sal, temp and p.
        This is based on the Jackett and McDougall (1995) equation of state
        for calculating the in situ density basing on potential temperature
        and salinity. The polinomial coefficients may be found within
        Jackett's paper (Table A1).
        NOTE: the pressure should be converted to BAR in order to use Jackett and
              McDougall's coefficients.
        """

        # Pressure conversion from [dbar] to [bar]
        ref_press /= 10
        # ==================================================================
        # Compute reference density at atmospheric pressure
        #
        #   rho = rho(sal, temp, 0) = rho_0 + A*sal + B*sal^3/2 + C*sal^2 .
        #
        # Notation follows 'International one-atmosphere equation of state
        # of seawater' (Millero and Poisson, 1981).
        # ==================================================================

        rho = EoS.__compute_rho(sal, pot_temp)

        # ==================================================================
        # Compute coefficients in the bulk modulus of seawater expression
        #
        #   K(sal, temp, p) = K_0 + Ap + Bp^2 , with K_0 = K(sal, temp, 0) .
        #
        # Each term is composed by a pure water term (subscript 'w') and
        # others involving pot. temperature and salinity:
        #   K_0 = Kw_0 + a*sal + b*sal^3/2
        #   A = Aw + c*sal + d*sal^3/2
        #   B = Bw + e*sal
        # Notation follows 'A new high pressure equation of state for
        # seawater' (Millero et al, 1980).
        # ==================================================================

        # Bulk modulus of seawater at atmospheric pressure.
        K_0 = EoS.__compute_K_0(sal, pot_temp)
        # Compression term coefficients.
        A = EoS.__compute_A(sal, pot_temp)
        B = EoS.__compute_B(sal, pot_temp)

        # ==================================================================
        # Compute IN SITU DENSITY IN TERMS OF DEPTH. The above
        # coeffients of terms in K(sal, temp, p) have been modified
        # consistently with Jackett and McDougall (1994).
        #
        #   density(sal, temp, press) = rho/[1 - press/K(sal, temp, press)]
        #                       = rho/[1 - press/(K_0 + (A*press + B*press^2))]
        # ==================================================================

        density = rho / (1.0 - ref_press / (K_0 + ref_press * (A + ref_press * B)))

        # Return density array.
        return density

    @staticmethod
    def potential_temperature(
        sal: float, temp: float, press: float, ref_press: float = 0
    ) -> float:
        """
        Compute potential temperature, from UNESCO (1983).

        :params sal, temp, press, ref_press : local salinity, local temperature, local pressure, reference pressure
        NOTE: pressure is expressed in [dbar]
        """

        H = ref_press - press
        XK = H * EoS.__adiabtempgrad(sal, temp, press)
        temp = temp + 0.5 * XK
        Q = XK
        press = press + 0.5 * H
        XK = H * EoS.__adiabtempgrad(sal, temp, press)
        temp = temp + 0.29289322 * (XK - Q)
        Q = 0.58578644 * XK + 0.121320344 * Q
        XK = H * EoS.__adiabtempgrad(sal, temp, press)
        temp = temp + 1.707106781 * (XK - Q)
        Q = 3.414213562 * XK - 4.121320344 * Q
        press = press + 0.5 * H
        XK = H * EoS.__adiabtempgrad(sal, temp, press)
        THETA = temp + (XK - 2.0 * Q) / 6.0
        return THETA

    @staticmethod
    def press2depth(press: float, latitude: float) -> float:
        """
        Conversion from pressure (dbars) to depth (m), as in UNESCO, 1983.
        """

        X = np.sin(latitude / 57.29578)
        X = X**2
        # GRAVITY VARIATION WITH LATITUDE: ANON (1970) BULLETIN GEODESIQUE
        GR = 9.780318 * (1.0 + (5.2788e-3 + 2.36e-5 * X) * X) + 1.092e-6 * press
        DEPTH = (
            ((-1.82e-15 * press + 2.279e-10) * press - 2.2512e-5) * press + 9.72659
        ) * press
        DEPTH = DEPTH / GR
        return DEPTH

    @staticmethod
    def depth2press(depth: float) -> float:
        """
        Conversion from depth (m) to pressure (dbars).
        As in NEMO, the pressure in decibars is approximated by the depth in meters.
        """
        return depth

    @staticmethod
    def __compute_rho(sal: float, temp: float) -> float:
        """
        Compute reference density at atmospheric pressure (where pot_temp = insitu_temp)

        rho = rho(sal, temp, 0) = rho_0 + A*sal + B*sal^3/2 + C*sal^2 .

        Notation follows 'International one-atmosphere equation of state
        of seawater' (Millero and Poisson, 1981).

        Arguments
        ---------
        temp : <class 'numpy.ndarray'>
            sea water potential temperature [°C]
        sal : <class 'numpy.ndarray'>
            sea water salinity [PSU]

        Returns
        -------
        rho: <class 'numpy.ndarray'>
            reference density of sea water at atmospheric pressure
        """

        # Square root of salinity.
        SR = np.sqrt(sal)
        # Density of pure water.
        rho_0 = (
            (
                ((6.536336e-9 * temp - 1.120083e-6) * temp + 1.001685e-4) * temp
                - 9.095290e-3
            )
            * temp
            + 6.793952e-2
        ) * temp + 999.842594
        # Coefficients involving salinity and pot. temperature.
        A = (
            ((5.3875e-9 * temp - 8.2467e-7) * temp + 7.6438e-5) * temp - 4.0899e-3
        ) * temp + 0.824493
        B = (-1.6546e-6 * temp + 1.0227e-4) * temp - 5.72466e-3
        C = 4.8314e-4
        # International one-atmosphere Eq. of State of seawater.
        rho = rho_0 + (A + B * SR + C * sal) * sal

        return rho

    @staticmethod
    def __compute_K_0(sal: float, temp: float) -> float:
        """
        Compute bulk modulus of seawater at atmospheric pressure term

        K_0 = Kw_0 + a*sal + b*sal^3/2

        Notation follows 'A new high pressure equation of state for
        seawater' (Millero et al, 1980), using coefficients from
        Jackett and McDougall (1995, Table A1).

        Arguments
        ---------
        temp : <class 'numpy.ndarray'>
            sea water potential temperature [°C]
        sal : <class 'numpy.ndarray'>
            sea water salinity [PSU]

        Returns
        -------
        K_0: <class 'numpy.ndarray'>
        bulk modulus of seawater at atmospheric pressure
        """

        # Square root of salinity.
        SR = np.sqrt(sal)
        # Bulk modulus of seawater at atmospheric pressure: pure water term
        Kw_0 = (
            ((-4.190253e-05 * temp + 9.648704e-03) * temp - 1.706103) * temp
            + 1.444304e02
        ) * temp + 1.965933e04
        # Coefficients involving salinity and pot. temperature.
        a = (
            (-5.084188e-05 * temp + 6.283263e-03) * temp - 3.101089e-01
        ) * temp + 5.284855e01
        b = (-4.619924e-04 * temp + 9.085835e-03) * temp + 3.886640e-01
        # Bulk modulus of seawater at atmospheric pressure.
        K_0 = Kw_0 + (a + b * SR) * sal

        return K_0

    @staticmethod
    def __compute_A(sal: float, temp: float) -> float:
        """
        Compute compression term coefficient A in bulk modulus of seawater

        A = Aw + c*sal + d*sal^3/2

        Notation follows 'A new high pressure equation of state for
        seawater' (Millero et al, 1980), using coefficients from
        Jackett and McDougall (1995, Table A1).

        Arguments
        ---------
        temp : <class 'numpy.ndarray'>
            sea water potential temperature [°C]
        sal : <class 'numpy.ndarray'>
            sea water salinity [PSU]

        Returns
        -------
        A: <class 'numpy.ndarray'>
        compression term coefficient A
        """

        # Square root of salinity.
        SR = np.sqrt(sal)
        # Compression term.
        Aw = (
            (1.956415e-06 * temp - 2.984642e-04) * temp + 2.212276e-02
        ) * temp + 3.186519
        c = (2.059331e-07 * temp - 1.847318e-04) * temp + 6.704388e-03
        d = 1.480266e-04
        A = Aw + (c + d * SR) * sal

        return A

    @staticmethod
    def __compute_B(sal: float, temp: float) -> float:
        """
        Compute compression term coefficient A in bulk modulus of seawater

        B = Bw + e*sal

        Notation follows 'A new high pressure equation of state for
        seawater' (Millero et al, 1980), using coefficients from
        Jackett and McDougall (1995, Table A1).

        Arguments
        ---------
        temp : <class 'numpy.ndarray'>
            sea water potential temperature [°C]
        sal : <class 'numpy.ndarray'>
            sea water salinity [PSU]

        Returns
        -------
        B: <class 'numpy.ndarray'>
        compression term coefficient B
        """

        # Compression term.
        Bw = (1.394680e-07 * temp - 1.202016e-05) * temp + 2.102898e-04
        e = (6.207323e-10 * temp + 6.128773e-08) * temp - 2.040237e-06
        B = Bw + e * sal

        return B

    @staticmethod
    def __adiabtempgrad(sal: float, temp: float, press: float) -> float:
        """
        Compute adiabatic lapse rate (adiabatic temperature gradient), from UNESCO (1983).

        :params sal, temp, press : salinity, temperature, pressure
        """

        DS = sal - 35.0
        ATG = (
            (
                ((-2.1687e-16 * temp + 1.8676e-14) * temp - 4.6206e-13) * press
                + (
                    (2.7759e-12 * temp - 1.1351e-10) * DS
                    + ((-5.4481e-14 * temp + 8.733e-12) * temp - 6.7795e-10) * temp
                    + 1.8741e-8
                )
            )
            * press
            + (-4.2393e-8 * temp + 1.8932e-6) * DS
            + ((6.6228e-10 * temp - 6.836e-8) * temp + 8.5258e-6) * temp
            + 3.5803e-5
        )
        return ATG


if __name__ == "__main__":
    # Test if _compute_rho() gives correct ref density at atm press. for
    # pure water (Sal = 0 PSU) and standard seawater (Sal = 35 PSU),
    # at Temperature = 5, 25 °C.
    # Reference values may be found within
    # 'Algorithms for computation of fundamental properties of seawater'
    # (UNESCO, 1983. Section 3, p.19)
    ref_sal = [0, 35]  # PSU
    ref_temp = [5, 25]  # °C
    ref_rho = [999.96675, 997.04796, 1027.67547, 1023.34306]  # kg/m^3
    out_rho = []
    for sal in ref_sal:
        for temp in ref_temp:
            out_rho.append(EoS._EoS__compute_rho(sal, temp))
    error = 1e-06  # kg/m^3
    assert np.allclose(ref_rho, out_rho, atol=error)

    # Test adiabatic lapse rate and potential temperature.
    # From UNESCO documentation.
    assert np.isclose(EoS._EoS__adiabtempgrad(40, 40, 10000), 3.255976e-4)
    assert np.isclose(EoS.potential_temperature(40, 40, 10000), 36.89073)

    # Test Compute density from Jackett and Mcdougall (1995).
    assert np.isclose(EoS.compute_density(35.5, 3.0, 3000), 1041.83267)
    # Test conversion from pressure to depth.
    # From UNESCO documentation.
    assert np.isclose(EoS.press2depth(10000, 30), 9712.653)

    # Check if it works for 4D array
    test_sal = np.random.rand(3, 10, 2, 15) * 35.5
    print(f"input salinity has dims {test_sal.shape}")
    test_temp = np.ones_like(test_sal) * 25
    test_4d = EoS.compute_density(test_sal, test_temp)
    print(f"4D density as shape {test_4d.shape}")
    try:
        EoS.compute_density(test_sal, test_temp[:, :, 0, :])
    except ValueError:
        print("Not working if temp and sal has different shape")
    EoS.compute_density(test_sal[0], test_temp[0, 0, :, :])
    EoS.compute_density(test_sal, test_temp[0, :, :])
    print("Working if the first dimension is missing from one of the two arrays")
