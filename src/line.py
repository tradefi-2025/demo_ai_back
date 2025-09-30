import torch
import math
def gaussian_1d(x, mu=0.0, sigma=1.0):
    """
    Compute the 1D Gaussian function.
    :param x: Input tensor of x-values.
    :param mu: Mean of the Gaussian.
    :param sigma: Standard deviation of the Gaussian.
    :return: Tensor of Gaussian values.
    """
    A = 1 / (sigma * torch.sqrt(torch.tensor(2 * math.pi)))
    exponent = -((x - mu)**2) / (2 * sigma**2)
    return A * torch.exp(exponent)

# Fixed rotate function
def rotate(a, b, theta_degrees):
    theta = theta_degrees * 2 * torch.pi / 360  # Convert to radians
    sin = torch.sin(theta)
    cos = torch.cos(theta)
    x_new = (a * cos + sin) / (cos + a * sin)
    return x_new, b


class Line:
    def __init__(self, a, b, mu=0, std=1, push=0, V=0.5, dt=1/390, weight_param=0, nature='S'):
        self.a_ = a
        self.b = b
        self.Cdistance = 0
        self.slope_v = torch.FloatTensor([1, a])
        self.slope_v /= self.slope_v.norm()
        self.ortho_v = torch.FloatTensor([[0, -1], [1, 0]]) @ self.slope_v
        self.std = std
        self.push = torch.FloatTensor([push]) if not isinstance(push, torch.Tensor) else push
        self.weight_param = weight_param
        self.V = V
        self.dt = torch.FloatTensor([dt])
        self.ignore = 0
        self.nature = nature
        self.max_gauss = gaussian_1d(torch.tensor([0.0]), 0, 1).item()

    def mu_base(self, mu1, w2, mu2, w3, mu3):
        return self.mu(mu1)

    def mu(self, mu):
        return (
            1.5 * self.std ** 2
            - (self.std * -self.V * 1.5) / (torch.sqrt(self.dt) * 0.5)
            - mu / 2
            + self.V * abs(mu)
        )

    def update_push(self, point):
        ort = self.ortho_P(point)
        dist = point - ort

        if dist[1] != 0:
            self.Cdistance += dist.norm() * (-dist[1] / abs(dist[1]))

        w = self.Cdistance
        w = -((-w) ** 0.5) if w < 0 else w ** 0.5
        self.push = torch.FloatTensor([w])

        if torch.isnan(self.push).any():
            print("Raise from push")
            print("ortho point:", ort)
            print("distance vector:", dist)
            print("cumulative distance:", self.Cdistance)

    @property
    def a(self):
        return self.a_

    @a.setter
    def a(self, value):
        self.a_ = value
        self.slope_v = torch.FloatTensor([1, value])
        self.slope_v /= self.slope_v.norm()
        self.ortho_v = torch.FloatTensor([[0, -1], [1, 0]]) @ self.slope_v

    def ortho_P(self, point):
        if self.a == 0:
            return torch.FloatTensor([point[0], self.b])

        ap = self.ortho_v[1] / self.ortho_v[0]
        bp = point[1] - ap * point[0]
        x = (bp - self.b) / (self.a - ap)

        if torch.isnan(x):
            print("raise from ortho_P")
            print("a:", self.a, "b:", self.b)
            print("slope_v:", self.slope_v)
            print("ortho_v:", self.ortho_v)
            print("bp:", bp)
            raise RuntimeError("NaN in ortho_P")

        return torch.FloatTensor([x, self.apply(x)])

    def apply(self, x):
        return self.a * x + self.b

    def w(self, point, pt_prec=None):
        if self.nature == 'B':
            ort1 = self.ortho_P(point)
            dist1 = point - ort1
            if dist1[1] == 0 and not (-1e-2 < dist1[0] < 1e-2):
                print("raise from WB1", self.a, self.b, point, dist1)

            ort2 = self.ortho_P(pt_prec)
            dist2 = pt_prec - ort2
            if dist2[1] == 0 and not (-1e-4 < dist2[0] < 1e-4):
                print("raise from WB2", self.a, self.b, pt_prec, dist2)

            w1 = gaussian_1d(dist1[1] * self.weight_param + self.push) * 0.5 / self.max_gauss
            w2 = (-gaussian_1d(dist2[1] * self.weight_param + self.push) + self.max_gauss) * 0.5 / self.max_gauss
            return w1 * w2 / (2 * self.max_gauss)

        if self.ignore:
            return 0

        ort = self.ortho_P(point)
        dist = point - ort
        if dist[1] == 0 and not (-1e-2 < dist[0] < 1e-2):
            print("raise from W", self.a, self.b, point, dist)

        x = -self.V * dist.norm() * (-1 if dist[1] > 0 else 1)
        weight = 0.5 * torch.exp(-(x * self.weight_param + self.push))

        if torch.isnan(weight).any():
            print("raise2 from W", self.a, self.b, point, dist, x, self.weight_param, self.push)

        return torch.min(weight, torch.FloatTensor([0.5]))


class PELevel:
    def __init__(self, data, dt=390):
        dt = torch.FloatTensor([1 / dt])
        rt = torch.log(data[1:] / data[:-1])
        std = rt.std() / torch.sqrt(dt)
        mu = rt.mean() / dt + (std ** 2) / 2

        self.PE = torch.sin(torch.arange(1, data.size(0) + 1))
        self.level = data @ self.PE

        self.mu = ((9 * std) / (2 * torch.sqrt(dt)) + (3 * std ** 2) / 4) * 2 - mu
        self.max_step = torch.exp((mu + (std ** 2) / 2) * dt + std * torch.sqrt(dt) * 3) * data.mean()
        self.C = torch.FloatTensor([torch.sum(self.PE[i:]) for i in range(data.size(0))]) * self.max_step / 10
        self.arctan_limit = torch.arctan(torch.FloatTensor([float('inf')]))

    def w(self, PE, i):
        return torch.arctan(-(PE - self.level) / (self.C[i] * self.PE[i])) * 0.5 / self.arctan_limit
