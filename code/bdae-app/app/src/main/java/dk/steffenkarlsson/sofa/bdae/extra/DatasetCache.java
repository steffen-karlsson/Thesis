package dk.steffenkarlsson.sofa.bdae.extra;

import java.util.ArrayList;
import java.util.List;

import dk.steffenkarlsson.sofa.bdae.IActivityHandler;
import dk.steffenkarlsson.sofa.bdae.entity.Dataset;
import dk.steffenkarlsson.sofa.bdae.request.GetDatasetsRequest;
import dk.steffenkarlsson.sofa.networking.Result;

/**
 * Created by steffenkarlsson on 6/5/16.
 */
public class DatasetCache {
    private static DatasetCache ourInstance = new DatasetCache();

    public static DatasetCache getInstance() {
        return ourInstance;
    }

    private DatasetCache() {
    }

    public enum RequestType {
        DATASETS
    }

    public interface OnDatasetReadyListener {
        void onReady(List<Dataset> datasets);
    }

    private static List<Dataset> DATASETS = null;

    private List<OnDatasetReadyListener> mReadyListener = new ArrayList<>();

    public void getDatasets(IActivityHandler activityHandler, final OnDatasetReadyListener readyListener) {
        if (DATASETS != null) {
            readyListener.onReady(DATASETS);
            return;
        }
        mReadyListener.add(readyListener);

        CustomRequestListener listener = new CustomRequestListener(activityHandler) {
            @Override
            protected void onData(int id, Result result) {
                DATASETS = (List<Dataset>) result.response;
                readyListener.onReady(DATASETS);
            }

            @Override
            public void onError(int id, int statusCode) {
                readyListener.onReady(null);
            }
        };

        new GetDatasetsRequest()
                .withContext(activityHandler.getActivity())
                .setOnRequestListener(listener)
                .run(RequestType.DATASETS);
    }

    public void clear() {
        DATASETS = null;
    }

    public void invalidate() {
        DATASETS = null;
        mReadyListener.clear();
    }
}
