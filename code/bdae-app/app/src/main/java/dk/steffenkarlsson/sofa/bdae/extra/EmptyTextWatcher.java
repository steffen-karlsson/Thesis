package dk.steffenkarlsson.sofa.bdae.extra;

import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.View;

import com.rengwuxian.materialedittext.MaterialEditText;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class EmptyTextWatcher implements TextWatcher {

    public interface OnValidateListener {
        void onValidate(int index,  boolean isValid, boolean hasChanged);
    }

    private final MaterialEditText mEditText;
    private final int mIndex;
    private OnValidateListener mOnValidateListener;
    private String mCurrentText;

    public EmptyTextWatcher(MaterialEditText editText, int index, OnValidateListener onValidateListener) {
        this.mEditText = editText;
        this.mCurrentText = editText.getText().toString();
        this.mIndex = index;
        this.mOnValidateListener = onValidateListener;

        mEditText.setOnFocusChangeListener(new View.OnFocusChangeListener() {
            @Override
            public void onFocusChange(View v, boolean hasFocus) {
                if (!hasFocus) {
                    EmptyTextWatcher.this.mCurrentText = mEditText.getText().toString();
                }
            }
        });
    }

    @Override
    public void beforeTextChanged(CharSequence s, int start, int count, int after) {
    }

    @Override
    public void onTextChanged(CharSequence s, int start, int before, int count) {
    }

    @Override
    public void afterTextChanged(Editable s) {
        boolean isEmpty = TextUtils.isEmpty(s.toString());
        if (isEmpty)
            mEditText.setError("Required Field");

        if (mOnValidateListener != null)
            mOnValidateListener.onValidate(mIndex, !isEmpty, !mCurrentText.equals(s.toString()));
    }
}