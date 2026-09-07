from .face_auth import authenticate_face
from .iris_auth import authenticate_iris


def authenticate_multimodal(
    face_image,
    iris_image,
    face_weight=0.5,
    iris_weight=0.5,
    final_threshold=0.70
):
    """
    Face + Iris multimodal authentication.

    Parameters
    ----------
    face_image : numpy.ndarray
        Face input image.

    iris_image : numpy.ndarray
        Iris input image.

    face_weight : float
        Weight for face score.

    iris_weight : float
        Weight for iris score.

    final_threshold : float
        Final authentication threshold.

    Returns
    -------
    dict
    """

    # --------------------------------------------------------
    # 1. Face authentication
    # --------------------------------------------------------

    face_result = authenticate_face(face_image)

    # --------------------------------------------------------
    # 2. Iris authentication
    # --------------------------------------------------------

    iris_result = authenticate_iris(iris_image)

    face_score = float(face_result.get("score", 0.0))
    iris_score = float(iris_result.get("score", 0.0))

    face_authenticated = bool(
        face_result.get("authenticated", False)
    )

    iris_authenticated = bool(
        iris_result.get("authenticated", False)
    )

    # --------------------------------------------------------
    # 3. Final score
    # --------------------------------------------------------

    final_score = (
        face_score * face_weight
        + iris_score * iris_weight
    )

    # --------------------------------------------------------
    # 4. Final authentication
    #
    # Both modalities must pass their own threshold,
    # and the weighted final score must pass the threshold.
    # --------------------------------------------------------

    is_authenticated = (
        face_authenticated
        and iris_authenticated
        and final_score >= final_threshold
    )

    # --------------------------------------------------------
    # 5. Name
    #
    # Current CASIA datasets have different ID systems,
    # so do not require face_name == iris_name here.
    # --------------------------------------------------------

    if is_authenticated:
        name = face_result.get("name")
    else:
        name = None

    return {
        "is_authenticated": is_authenticated,
        "name": name,
        "final_score": round(final_score, 4),
        "details": {
            "face_authenticated": face_authenticated,
            "iris_authenticated": iris_authenticated,
            "face_score": round(face_score, 4),
            "iris_score": round(iris_score, 4)
        }
    }
