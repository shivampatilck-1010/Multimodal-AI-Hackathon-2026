from __future__ import annotations

import httpx

BASE_URL = "http://127.0.0.1:8080"
COURSE_ID = "cs229"

UNITS = [
    {
        "id": "cs229_optimization_01",
        "course_id": COURSE_ID,
        "text": (
            "Optimization is the process of finding model parameters that minimize "
            "a loss function or maximize an objective function. In machine learning, "
            "optimization is used to learn parameters from training data."
        ),
        "topic": "Optimization",
        "subtopic": "Optimization Fundamentals",
        "concept": "Optimization",
        "source": {
            "type": "pdf",
            "file_name": "CS229_Optimization_Notes.pdf",
            "page": 1,
        },
        "metadata": {
            "demo_seed": True,
            "source_description": "CS229 optimization course notes",
        },
    },
    {
        "id": "cs229_optimization_02",
        "course_id": COURSE_ID,
        "text": (
            "Gradient descent is an iterative optimization algorithm. Starting from "
            "an initial parameter vector, the algorithm computes the gradient of the "
            "objective function and updates the parameters in the opposite direction "
            "of the gradient. The learning rate controls the size of each update."
        ),
        "topic": "Optimization",
        "subtopic": "Gradient Descent",
        "concept": "Gradient Descent",
        "source": {
            "type": "slide",
            "file_name": "CS229_Optimization_Lecture.pptx",
            "slide": 12,
        },
        "metadata": {
            "demo_seed": True,
            "source_description": "CS229 optimization lecture slides",
        },
    },
    {
        "id": "cs229_optimization_03",
        "course_id": COURSE_ID,
        "text": (
            "For a differentiable objective function J(theta), gradient descent "
            "updates the parameters according to theta := theta - alpha grad J(theta), "
            "where alpha is the learning rate. The update moves the parameters toward "
            "a local direction of decreasing objective value."
        ),
        "topic": "Optimization",
        "subtopic": "Gradient Descent",
        "concept": "Gradient Descent Update Rule",
        "source": {
            "type": "video",
            "file_name": "CS229_Optimization_Lecture.mp4",
            "timestamp_start": "00:18:00",
            "timestamp_end": "00:20:30",
        },
        "metadata": {
            "demo_seed": True,
            "source_description": "CS229 optimization lecture recording",
        },
    },
    {
        "id": "cs229_regression_01",
        "course_id": COURSE_ID,
        "text": (
            "Linear regression models the relationship between input variables and "
            "a continuous target using a linear function. The parameters are commonly "
            "estimated by minimizing the squared error between predictions and targets."
        ),
        "topic": "Regression",
        "subtopic": "Linear Regression",
        "concept": "Linear Regression",
        "source": {
            "type": "pdf",
            "file_name": "CS229_Regression_Notes.pdf",
            "page": 3,
        },
        "metadata": {
            "demo_seed": True,
        },
    },
    {
        "id": "cs229_neural_networks_01",
        "course_id": COURSE_ID,
        "text": (
            "A neural network consists of layers of computational units. Each unit "
            "computes a weighted combination of its inputs followed by a nonlinear "
            "activation function. Multiple layers allow the network to represent "
            "complex nonlinear functions."
        ),
        "topic": "Neural Networks",
        "subtopic": "Network Architecture",
        "concept": "Neural Network Architecture",
        "source": {
            "type": "slide",
            "file_name": "CS229_Neural_Networks_Lecture.pptx",
            "slide": 8,
        },
        "metadata": {
            "demo_seed": True,
        },
    },
    {
        "id": "cs229_backprop_01",
        "course_id": COURSE_ID,
        "text": (
            "Backpropagation computes gradients of a loss function with respect to "
            "network parameters by applying the chain rule from the output layer "
            "back through the network. These gradients can then be used by an "
            "optimization algorithm such as gradient descent."
        ),
        "topic": "Backpropagation",
        "subtopic": "Gradient Computation",
        "concept": "Backpropagation",
        "source": {
            "type": "video",
            "file_name": "CS229_Backpropagation_Lecture.mp4",
            "timestamp_start": "00:11:00",
            "timestamp_end": "00:14:00",
        },
        "metadata": {
            "demo_seed": True,
        },
    },
    {
        "id": "cs229_linear_algebra_01",
        "course_id": COURSE_ID,
        "text": (
            "Vectors and matrices provide the mathematical representation used "
            "throughout machine learning. Matrix multiplication is used to transform "
            "feature vectors and represent linear transformations efficiently."
        ),
        "topic": "Linear Algebra",
        "subtopic": "Vectors and Matrices",
        "concept": "Vectors and Matrices",
        "source": {
            "type": "pdf",
            "file_name": "CS229_Linear_Algebra_Notes.pdf",
            "page": 5,
        },
        "metadata": {
            "demo_seed": True,
        },
    },
]


def main() -> None:
    print("=" * 70)
    print("CS229 KNOWLEDGE BASE SEED")
    print("=" * 70)

    print(f"Backend: {BASE_URL}")
    print(f"Course:  {COURSE_ID}")
    print(f"Units:   {len(UNITS)}")
    print()

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        response = client.post(
            "/api/kb/ingest",
            json={"units": UNITS},
        )

        print("HTTP:", response.status_code)

        try:
            payload = response.json()
            print("Response:")
            print(payload)
        except Exception:
            print(response.text)

        response.raise_for_status()

    print()
    print("CS229 ingestion completed.")


if __name__ == "__main__":
    main()