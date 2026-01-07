import hiero.core
import hiero.ui


def reproduce_bug():
    projects = hiero.core.projects()
    if not projects:
        return

    sequences = projects[0].sequences()
    if not sequences:
        return

    seq = sequences[0]
    hiero.ui.openInTimeline(seq)


if __name__ == "__main__":
    reproduce_bug()

